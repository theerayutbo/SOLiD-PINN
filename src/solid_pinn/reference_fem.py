"""Independent P1 Galerkin reference; no ReducedP2D calls."""
from dataclasses import dataclass
import numpy as np
from scipy.linalg import solve
from scipy.optimize import root
from scipy.integrate import solve_ivp
from .parameters import Parameters
from .ocv import ocv_v


def matrices(n, spherical=False):
    """P1 mass/stiffness on [0,1]; three-point Gauss integrates exactly."""
    nodes = np.linspace(0, 1, n+1)
    m = np.zeros((n+1,n+1)); k = m.copy()
    z,w = np.polynomial.legendre.leggauss(3)
    for i in range(n):
        h = nodes[i+1]-nodes[i]
        for q,weight in zip(z,w):
            t=(q+1)/2; b=np.array([1-t,t]); d=np.array([-1.,1.])/h
            factor=weight*h/2 * ((nodes[i]+t*h)**2 if spherical else 1.)
            m[i:i+2,i:i+2] += factor*np.outer(b,b)
            k[i:i+2,i:i+2] += factor*np.outer(d,d)
    return nodes,m,k


@dataclass
class Fields:
    voltage: float
    electrolyte: np.ndarray
    solid: np.ndarray
    reaction: np.ndarray


class ReferenceFEM:
    def __init__(self, params=None, nx=8, nr=12, ocv_function=ocv_v):
        if nx<2 or nr<3:
            raise ValueError('nx >= 2 and nr >= 3')
        self.p=params or Parameters(); self.ocv=ocv_function
        self.x,m,k=matrices(nx); self.r,mr,kr=matrices(nr,True)
        self.wx=m.sum(axis=0); self.wr=mr.sum(axis=0)*3
        p=self.p; self.aL=p.active_surface_area_m_inv*p.cathode_m
        self.beta=p.faraday_c_mol/(2*p.gas_constant_j_mol_k*p.temperature_k)
        ke=k*p.kappa_cathode_effective/p.cathode_m
        ks=k*p.sigma_cathode_s_m/p.cathode_m
        self.e=np.zeros_like(m); self.s=np.zeros_like(m)
        self.e[1:,:]=solve(ke[1:,1:],-self.aL*m[1:,:],assume_a='pos')
        self.s[:-1,:]=solve(ks[:-1,:-1],self.aL*m[:-1,:],assume_a='pos')
        self.delta=self.s-self.e
        self.radial=solve(mr,-kr,assume_a='pos')*p.particle_diffusivity_m2_s/p.particle_radius_m**2
        endpoint=np.zeros(nr+1); endpoint[-1]=1
        self.flux=solve(mr,endpoint,assume_a='pos')/(p.faraday_c_mol*p.particle_radius_m*p.max_solid_concentration_mol_m3)

    def fields(self, surface_fraction, current, stage):
        p=self.p; J=current/p.area_m2
        u=self.ocv(1-np.asarray(surface_fraction),stage)
        if u.shape != self.x.shape or not np.all(np.isfinite(u)):
            raise ValueError('invalid surface state/OCV')
        left=-np.arcsinh(J/(2*p.exchange_current_lithium_a_m2))/self.beta-J*p.separator_m/p.kappa_sse_s_m
        j0=p.exchange_current_cathode_a_m2; n=len(self.x)
        def res(z):
            j=z[:n]; v=z[-1]
            return np.r_[v-left+self.delta@j-u+np.arcsinh(j/(2*j0))/self.beta, (self.aL*(self.wx@j)-J)/self.aL]
        def jac(z):
            j=z[:n]; a=self.delta+np.diag(1/(self.beta*np.sqrt((2*j0)**2+j*j)))
            return np.block([[a,np.ones((n,1))],[self.wx[None,:],np.zeros((1,1))]])
        initial=np.r_[np.full(n,J/self.aL),float(np.mean(u))+left-np.arcsinh(J/self.aL/(2*j0))/self.beta]
        ans=root(res,initial,jac=jac,tol=1e-10)
        if not np.all(np.isfinite(ans.x)) or np.max(np.abs(res(ans.x)))>1e-9:
            raise RuntimeError('independent axial nonlinear solve failed')
        j=ans.x[:n]; v=float(ans.x[-1]); return Fields(v,left+self.e@j,v+self.s@j,j)

    def soc(self, c):
        return float(1-self.wx@c@self.wr)

    def stage(self, stage, rate, c0=None, max_step=300., rtol=1e-7, atol=1e-9):
        if stage not in ('charge','discharge') or rate<=0 or max_step<=0:
            raise ValueError('invalid stage/rate/step')
        p=self.p; shape=(len(self.x),len(self.r)); current=p.current_a(rate)*(-1 if stage=='charge' else 1)
        c=np.full(shape,1-p.initial_soc) if c0 is None else np.array(c0, dtype=float)
        if c.shape!=shape or not np.all(np.isfinite(c)):
            raise ValueError('invalid initial state')
        def rhs(t,y):
            a=y.reshape(shape); f=self.fields(a[:,-1],current,stage)
            return (a@self.radial.T+f.reaction[:,None]*self.flux).ravel()
        def event(t,y):
            a=y.reshape(shape); v=self.fields(a[:,-1],current,stage).voltage; soc=self.soc(a)
            return min(p.upper_cutoff_v-v,.995-soc) if stage=='charge' else min(v-p.lower_cutoff_v,soc-.005)
        event.terminal=True; event.direction=-1
        if event(0,c.ravel())<=0:
            return np.array([0.]),c[None,:,:]
        ans=solve_ivp(rhs,(0,rate*1.25*3600),c.ravel(),method='BDF',max_step=max_step,rtol=rtol,atol=atol,events=event,dense_output=True)
        if not ans.success: raise RuntimeError(ans.message)
        t=np.r_[np.arange(0,ans.t[-1],max_step),ans.t[-1]]
        return t,ans.sol(t).T.reshape((-1,*shape))
