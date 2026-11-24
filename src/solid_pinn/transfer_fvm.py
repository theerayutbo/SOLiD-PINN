"""Cell-centred conservative FVM for the transferred C/20 model.

Shares stage integrator and material laws, independently discretises charge
and radial diffusion. Outer shell average approximates surface occupancy.
"""
import numpy as np
from scipy.optimize import root
from .comsol_transfer import TransferFEM, table
from .reference_fem import Fields
from .parameters import Parameters
from dataclasses import replace


class TransferFVM(TransferFEM):
    def __init__(self,m,nx=8,nr=20):
        if nx<2 or nr<3: raise ValueError('nx >= 2 and nr >= 3')
        self.m=m; self.use_R=self.use_D=self.use_kinetics=True
        self.p=p=replace(Parameters(),area_m2=m['area'],separator_m=m['Ls'],cathode_m=m['L'],particle_radius_m=m['rp'],kappa_sse_s_m=m['kappa'],sigma_cathode_s_m=m['sigma']*m['fs'],cathode_ionic_phase_fraction=m['epsl'],max_solid_concentration_mol_m3=m['cmax'],temperature_k=m['T'],faraday_c_mol=m['F'],gas_constant_j_mol_k=m['R'],theoretical_capacity_mah_g=m['capacity'],nmc_loading_mg_cm2=m['loading'],exchange_current_cathode_a_m2=m['j0'],exchange_current_lithium_a_m2=m['j0li'],initial_soc=m['wdch']-m['wch'],particle_diffusivity_m2_s=m['D'])
        self.x=(np.arange(nx)+.5)/nx;self.r=(np.arange(nr)+.5)/nr
        self.wx=np.full(nx,1/nx); rf=np.linspace(0,1,nr+1)
        self.vol=np.diff(rf**3)/3;self.wr=3*self.vol;self.rf=rf
        self.aL=3*m['eps']/m['rp']*m['L'];self.beta=p.faraday_c_mol/(2*p.gas_constant_j_mol_k*p.temperature_k)
        dx=m['L']/nx;self.dx=dx
        # Face currents from cumulative reaction, half-cell boundary distances.
        self.e=np.zeros((nx,nx));self.s=np.zeros_like(self.e)
        for k in range(nx):
            b=np.eye(nx)[k]; ie=self.aL/nx*np.r_[np.cumsum(b[::-1])[::-1],0.]; iss=self.aL/nx*np.r_[0.,np.cumsum(b)]
            self.e[:,k]=-dx/p.kappa_cathode_effective*(.5*ie[0]+np.r_[0.,np.cumsum(ie[1:-1])])
            self.s[:,k]=dx/p.sigma_cathode_s_m*(.5*iss[-1]+np.r_[np.cumsum(iss[1:-1][::-1])[::-1],0.])
        self.delta=self.s-self.e

    def fields(self,theta,current,stage):
        m=self.m;p=self.p;J=current/p.area_m2;theta=np.asarray(theta)
        if stage=='charge':
            arg=100*(1-(m['wdch']-m['wch'])-theta)/m['wch'];u=table(m,'Uch',np.clip(arg,0,100))-J*table(m,'Rc_node',theta)
        else:
            arg=100*(theta-(1-m['wdch']))/m['wdch'];u=table(m,'Udis',np.clip(arg,0,100))-J*table(m,'Rd_node',theta)
        x=np.clip(theta,.001,.999);j0=m['j0']*2*np.sqrt(x*(1-x));n=len(x)
        left=-np.arcsinh(J/(2*m['j0li']))/self.beta-J*m['Ls']/m['kappa']
        def res(z):
            j=z[:n]; return np.r_[z[-1]-left+self.delta@j-u+np.arcsinh(j/(2*j0))/self.beta, self.wx@j-J/self.aL]
        def jac(z):
            j=z[:n]; return np.block([[self.delta+np.diag(1/(self.beta*np.sqrt((2*j0)**2+j*j))),np.ones((n,1))],[self.wx[None,:],np.zeros((1,1))]])
        z=root(res,np.r_[np.full(n,J/self.aL),np.mean(u)+left],jac=jac,tol=1e-10)
        if not np.isfinite(z.x).all() or np.max(abs(res(z.x)))>1e-8:raise RuntimeError('FVM axial solve failed')
        j=z.x[:n];v=float(z.x[-1]);return Fields(v,left+self.e@j,v+self.s@j,j)

    def rhs(self,c,current,stage):
        f=self.fields(c[:,-1],current,stage)
        name='Ds_delithiation_theta' if stage=='charge' else 'Ds_lithiation_theta'
        d=table(self.m,name,.5*(c[:,:-1]+c[:,1:]))
        flux=d*self.rf[1:-1]**2*np.diff(c,axis=1)*len(self.r)/self.p.particle_radius_m**2
        out=np.zeros_like(c);out[:,:-1]+=flux;out[:,1:]-=flux
        out[:,-1]+=f.reaction/(self.p.faraday_c_mol*self.p.particle_radius_m*self.p.max_solid_concentration_mol_m3)
        return out/self.vol
