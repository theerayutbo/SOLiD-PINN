"""Approximate FEM transfer of saved COMSOL C20 settings; no refitting."""
import re, zipfile
import xml.etree.ElementTree as ET
from io import BytesIO
from dataclasses import replace
import numpy as np
import pandas as pd
from scipy.linalg import solve
from scipy.optimize import root
from scipy.integrate import solve_ivp
from .parameters import Parameters
from .reference_fem import ReferenceFEM, matrices, Fields


def read_model(path):
    with zipfile.ZipFile(path) as z:
        if 'dmodel.xml' in z.namelist():
            raw=z.read('dmodel.xml')
        else:
            names=[n for n in z.namelist() if n.lower().endswith('.mph')]
            if len(names)!=1: raise ValueError('expected one MPH file')
            with zipfile.ZipFile(BytesIO(z.read(names[0]))) as mph:
                raw=mph.read('dmodel.xml')
    tree=ET.fromstring(raw)
    p={e.get('name'):e.get('expr') for e in tree.findall('./ModelParam/expressions')}
    def num(k): return float(p[k].split('[')[0].strip())
    def setting(tag,key):
        return tree.find(f'.//PhysicsFeature[@tag="{tag}"]/param[@param="{key}"]').attrib['value'].split("'",2)[1]
    if p['csini_pe']!='csmax_pe*(1-(Wdch-Wch))' or p['i0ref_pe']!='10^log [A/m^2]': raise ValueError('unexpected parameter formula')
    if setting('pce1','IonicCorrModel')!='Bruggeman' or setting('pce1','fs')!='0.3159^1.5' or setting('per1','ElectrodeKinetics')!='LithiumInsertion': raise ValueError('unexpected physics settings')
    tables={};wanted={'Uch','Udis','Ds_delithiation_theta','Ds_lithiation_theta','Rc_node','Rd_node'}
    for f in tree.iter('FunctionFeature'):
        props={v.get('name'):v.get('value') or v.get('valueMatrix') for v in f.findall('propertyValue')}
        name=props.get('p:funcname')
        if name not in wanted:continue
        pairs=re.findall(r"\|2,'([^']+)','([^']+)'",props['p:table'])
        a=np.array([(float(x),num(y) if y in p else float(y)) for x,y in pairs])
        if len(a)<2 or not np.isfinite(a).all() or np.any(np.diff(a[:,0])<=0):raise ValueError('invalid table: '+name)
        tables[name]=a
    if set(tables)!=wanted:raise ValueError('missing tables')
    return dict(eps=num('eps_pe'),epsl=float(setting('pce1','epsl')),fs=.3159**1.5,wch=num('Wch'),wdch=num('Wdch'),j0=10**num('log'),j0li=float(setting('er1','i0').split('[')[0]),sigma=num('sigma_pe'),kappa=num('sigma_sse'),L=num('L_pe'),Ls=num('L_sep'),rp=num('rp_pe'),cmax=num('csmax_pe'),T=num('Tref'),F=num('F'),R=num('R'),area=num('A_cell'),loading=num('Cell_mass'),capacity=num('cap_NMC_ch'),D=num('D1ref_pe'),tables=tables)


def table(m,name,x):
    a=m['tables'][name];return np.interp(x,a[:,0],a[:,1])


class TransferFEM(ReferenceFEM):
    """Fixed phase fractions, linear interpolation, approximate insertion kinetics."""
    def __init__(self,m,nx=4,nr=10,use_R=True,use_D=True,use_kinetics=True):
        self.m=m;self.use_R=use_R;self.use_D=use_D;self.use_kinetics=use_kinetics
        p=replace(Parameters(),area_m2=m['area'],separator_m=m['Ls'],cathode_m=m['L'],particle_radius_m=m['rp'],kappa_sse_s_m=m['kappa'],sigma_cathode_s_m=m['sigma']*m['fs'],cathode_ionic_phase_fraction=m['epsl'],max_solid_concentration_mol_m3=m['cmax'],temperature_k=m['T'],faraday_c_mol=m['F'],gas_constant_j_mol_k=m['R'],theoretical_capacity_mah_g=m['capacity'],nmc_loading_mg_cm2=m['loading'],exchange_current_cathode_a_m2=m['j0'],exchange_current_lithium_a_m2=m['j0li'],initial_soc=m['wdch']-m['wch'],particle_diffusivity_m2_s=m['D'])
        super().__init__(p,nx,nr)
        self.aL=3*m['eps']/m['rp']*m['L']
        _,mass,k=matrices(nx);ke=k*p.kappa_cathode_effective/p.cathode_m;ks=k*p.sigma_cathode_s_m/p.cathode_m
        self.e[1:,:]=solve(ke[1:,1:],-self.aL*mass[1:,:],assume_a='pos')
        self.s[:-1,:]=solve(ks[:-1,:-1],self.aL*mass[:-1,:],assume_a='pos');self.delta=self.s-self.e
        _,mr,_=matrices(nr,True);self.inv_mass=np.linalg.inv(mr)
        self.edge_k=np.diff(self.r**3)/3/np.diff(self.r)**2
    def fields(self,theta,current,stage):
        m=self.m;p=self.p;theta=np.asarray(theta);J=current/p.area_m2
        if stage=='charge':
            arg=100*(1-(m['wdch']-m['wch'])-theta)/m['wch'];u=table(m,'Uch',np.clip(arg,0,100));rc=table(m,'Rc_node',theta)
        else:
            arg=100*(theta-(1-m['wdch']))/m['wdch'];u=table(m,'Udis',np.clip(arg,0,100));rc=table(m,'Rd_node',theta)
        if self.use_R:u=u-J*rc
        j0=p.exchange_current_cathode_a_m2
        if self.use_kinetics:
            x=np.clip(theta,.001,.999);j0=j0*2*np.sqrt(x*(1-x))
        left=-np.arcsinh(J/(2*p.exchange_current_lithium_a_m2))/self.beta-J*p.separator_m/p.kappa_sse_s_m
        n=len(self.x)
        def res(z):
            j=z[:n];return np.r_[z[-1]-left+self.delta@j-u+np.arcsinh(j/(2*j0))/self.beta,(self.aL*(self.wx@j)-J)/self.aL]
        def jac(z):
            j=z[:n];return np.block([[self.delta+np.diag(1/(self.beta*np.sqrt((2*j0)**2+j*j))),np.ones((n,1))],[self.wx[None,:],np.zeros((1,1))]])
        z=root(res,np.r_[np.full(n,J/self.aL),np.mean(u)+left],jac=jac,tol=1e-10)
        if not np.isfinite(z.x).all() or np.max(abs(res(z.x)))>1e-8:raise RuntimeError('axial solve failed')
        j=z.x[:n];v=float(z.x[-1]);return Fields(v,left+self.e@j,v+self.s@j,j)
    def rhs(self,c,current,stage):
        f=self.fields(c[:,-1],current,stage)
        if not self.use_D:return c@self.radial.T+f.reaction[:,None]*self.flux
        name='Ds_delithiation_theta' if stage=='charge' else 'Ds_lithiation_theta'
        d=table(self.m,name,.5*(c[:,:-1]+c[:,1:]));flux=d*self.edge_k*np.diff(c,axis=1)/self.p.particle_radius_m**2
        out=np.zeros_like(c);out[:,:-1]+=flux;out[:,1:]-=flux
        return out@self.inv_mass.T+f.reaction[:,None]*self.flux
    def stage(self,stage,rate,c0=None,max_step=120.,rtol=1e-7,atol=1e-9):
        current=self.p.current_a(rate)*(-1 if stage=='charge' else 1)
        shape=(len(self.x),len(self.r));c=np.full(shape,1-self.p.initial_soc) if c0 is None else c0
        def event(t,y):
            v=self.fields(y.reshape(shape)[:,-1],current,stage).voltage
            return 4.2-v if stage=='charge' else v-2.7
        event.terminal=True;event.direction=-1
        if event(0,c.ravel())<=0:raise RuntimeError('initial voltage outside stage range')
        sol=solve_ivp(lambda t,y:self.rhs(y.reshape(shape),current,stage).ravel(),(0,rate*1.6*3600),c.ravel(),method='BDF',max_step=max_step,rtol=rtol,atol=atol,events=event,dense_output=True)
        if not sol.success or not len(sol.t_events[0]):raise RuntimeError('voltage event not reached: '+sol.message)
        t=np.r_[np.arange(0,sol.t[-1],min(max_step,30.)),sol.t[-1]];cs=sol.sol(t).T.reshape((-1,*shape))
        if cs.min()<-1e-5 or cs.max()>1+1e-5:raise RuntimeError('unphysical concentration')
        v=np.array([self.fields(q[:,-1],current,stage).voltage for q in cs]);theta=np.array([self.wx@q@self.wr for q in cs])
        return pd.DataFrame(dict(time_h=t/3600,voltage_v=v,cell_soc=1-theta,stage=stage,rate=rate)),cs[-1]
