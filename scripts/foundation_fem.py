"""Independent P1 Galerkin x-r spatial discretization of the canonical model.
Axial reaction is mass-lumped; radial mass is consistent. Same material assumptions
as canonical_fv, not a separate physical model or a COMSOL run.
"""
import numpy as np
from scipy.linalg import solve
from scipy.optimize import root
from canonical_fv import Params


def matrices(n, length, spherical=False):
    x=np.linspace(0,length,n+1);M=np.zeros((n+1,n+1));K=M.copy()
    z,w=np.polynomial.legendre.leggauss(3)
    for i in range(n):
        h=x[i+1]-x[i]
        for q,wt in zip(z,w):
            t=(q+1)/2;N=np.array([1-t,t]);d=np.array([-1.,1.])/h
            f=wt*h/2*((x[i]+t*h)**2 if spherical else 1.)
            M[i:i+2,i:i+2]+=f*np.outer(N,N);K[i:i+2,i:i+2]+=f*np.outer(d,d)
    return M,K


class FEM:
    def __init__(self,p=Params(),nx=4,nr=12):
        p.validate();self.p=p;self.n=nx+1;self.m=nr+1;self.a=3*p.eps/p.R
        self.beta=p.F/(2*p.gas*p.T)
        M,K=matrices(nx,p.L);self.wx=M.sum(0);self.x=np.linspace(0,p.L,self.n)
        Mr,Kr=matrices(nr,p.R,True);self.w=Mr.sum(0)/Mr.sum()
        self.L=solve(Mr,-p.D*Kr,assume_a='pos');e=np.zeros(self.m);e[-1]=1
        self.b=solve(Mr,e,assume_a='pos')*p.R**2/(p.F*p.cmax)
        # Independent stiffness solves with reference electrolyte potential at x=0
        # and solid potential at x=L. The flux balance is enforced separately.
        self.E=np.zeros_like(M);self.H=np.zeros_like(M)
        self.E[1:,1:]=solve(p.kcat*K[1:,1:],np.eye(nx),assume_a='pos')
        self.H[:-1,:-1]=solve(p.scat*K[:-1,:-1],np.eye(nx),assume_a='pos')
        self.K=self.E+self.H
    def mean(self,c):return float(self.wx@(c@self.w)/self.p.L)
    def fields(self,c,J):
        p=self.p;surf=c[:,-1];u=4.4-1.9*surf;scale=2*p.j0*self.a*self.wx
        ext=J*p.S/p.ksep+np.arcsinh(J/(2*p.jli))/self.beta
        def res(z):
            q=z[:-1];return np.r_[self.K@q+np.arcsinh(q/scale)/self.beta+z[-1]-u,q.sum()-J]
        def jac(z):return np.block([[self.K+np.diag(1/(self.beta*np.sqrt(scale**2+z[:-1]**2))),np.ones((self.n,1))],[np.ones((1,self.n)),np.zeros((1,1))]])
        z=root(res,np.r_[J*self.wx/p.L,u.mean()],jac=jac,tol=1e-10).x
        err=float(np.max(abs(res(z))))
        if not np.isfinite(err) or err>1e-8:raise RuntimeError('FEM reaction solve failed')
        return z[-1]-ext,z[:-1],surf,err
    def rhs(self,c,q):return c@self.L.T+(q/(self.a*self.wx))[:,None]*self.b
