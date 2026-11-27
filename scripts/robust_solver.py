"""Reduced x-r electrochemical bridge with resistance coupled into reaction solve."""
import argparse,json,platform,time
from functools import lru_cache
from pathlib import Path
import numpy as np
import scipy
from scipy.linalg import expm
from scipy.optimize import least_squares
from hybrid_p2d import DT,JS,BLOCKS,profile,rates,missing,METHODS
TRUTHS=('null','rest','peak'); NOISE=(1.,5.); SEEDS=(11,23,37)
FIT=(32,48,4); REF=(64,96,16); LIMIT=1.
TRUE=np.array([.35,.7,1.]); SCALE=1.2

@lru_cache(maxsize=16)
def operators(n,m,sub,diffusion=1.):
    edges=np.linspace(0,1,m+1);w=np.diff(edges**3);rbar=.75*np.diff(edges**4)/w
    bs=np.array([[float(i>=k) for i in range(n)] for k in range(1,n)]);be=1-bs
    A=n*.35*np.eye(n)+.25/n*bs.T@bs+.7/n*be.T@be
    L=np.zeros((m,m))
    for k in range(1,m):
        f=3*.06*diffusion*(k/m)**2*m;L[k-1,k-1]-=f/w[k-1];L[k-1,k]+=f/w[k-1];L[k,k-1]+=f/w[k];L[k,k]-=f/w[k]
    s=np.zeros(m);e=(1-rbar[-1])/(rbar[-1]-rbar[-2]);s[-1]=1+e;s[-2]=-e
    b=np.zeros(m);b[-1]=n/w[-1]
    aug=np.zeros((m+1,m+1));aug[:m,:m]=L;aug[:m,m]=b
    H=expm(DT/(2*sub)*aug);E=H@H
    return w,A,s,H[:m,:m],H[:m,m],E[:m,:m],E[:m,m],.5+(np.arange(n)+.5)/n

def reaction(U,J,x,A,pattern,shift=0.):
    n=len(pattern);K=np.broadcast_to(A,(len(J),n,n)).copy();ix=np.arange(n)
    K[:,ix,ix]+=n*SCALE*x[:,None]*pattern+shift
    q=np.linalg.solve(K,np.stack([U.T,np.ones_like(U.T)],axis=-1));V=(q[:,:,0].sum(1)-J)/q[:,:,1].sum(1)
    p=(q[:,:,0]-V[:,None]*q[:,:,1]).T
    return p,V,K

def advance(x,a,d,h):
    z=a+d
    return x*np.exp(-z*h)+np.divide(a*(-np.expm1(-z*h)),z,out=np.zeros_like(z),where=z>0)

def simulate(j,method,params,truth,mesh=FIT,diagnostic=False,diffusion=1.,kinetic=1.,series=0.):
    n,m,sub=mesh;w,A,s,H,F,E,G,pattern=operators(n,m,sub,diffusion);A=A+n*.35*(kinetic-1)*np.eye(n);h=DT/sub
    c=np.full((n,m,j.shape[1]),.5);x=np.zeros(j.shape[1]);target=np.full(j.shape[1],.5)
    a,d=rates(method,params,truth,abs(j));out=[];flux=[]
    check=dict(mass=0.,charge=0.,power=0.,min_dissipation=0.,min_c=1.,max_c=0.,min_surface=1.,max_surface=0.,min_x=1.,max_x=0.)
    for k,u in enumerate(j):
        J=JS*u;surface=np.einsum('m,amc->ac',s,c);U=4.1-.8*surface;p,V,K=reaction(U,J,x,A,pattern)
        out.append(V-(.25+(.25+.7)/(2*n)+series)*J)
        if diagnostic:
            flux.append(p.copy());diss=np.einsum('ac,cab,bc->c',p,K,p)
            check['mass']=max(check['mass'],float(np.max(abs(np.einsum('m,amc->c',w,c)/n-target))))
            check['charge']=max(check['charge'],float(np.max(abs(p.sum(0)-J))),float(np.max(abs(np.einsum('cab,bc->ac',K,p)+V-U))))
            check['power']=max(check['power'],float(np.max(abs(np.sum(U*p,axis=0)-V*J-diss))))
            check['min_dissipation']=min(check['min_dissipation'],float(diss.min()))
            for name,z in [('c',c),('surface',surface),('x',x)]:
                check['min_'+name]=min(check['min_'+name],float(z.min()));check['max_'+name]=max(check['max_'+name],float(z.max()))
        if k==len(j)-1:break
        for step in range(sub):
            xm=advance(x,a[k],d[k],h/2);free=H@c;U0=4.1-.8*np.einsum('m,amc->ac',s,free)
            pm,_,_=reaction(U0,J,xm,A,pattern,.8*(s@F))
            c=E@c+G[None,:,None]*pm[:,None,:];x=advance(x,a[k],d[k],h);target+=h*J
    return np.array(out),check,np.array(flux)

