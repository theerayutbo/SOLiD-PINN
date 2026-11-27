"""Native PyBaMM spatial discretisation of the canonical single-ion ASSB PDE/DAE.

This is not the liquid-electrolyte DFN. It uses the same synthetic parameters
as canonical_fv, but assembles spatial operators through PyBaMM.
"""
from dataclasses import asdict
from pathlib import Path
import argparse,json,platform,importlib.metadata
import numpy as np
import pybamm
from canonical_fv import Params,Solver
from foundation_fem import FEM
from verify_foundation import cycle,compare

CONFIGS=(('coarse',8,24,150.,1e-8),('fine',16,48,150.,1e-8),('tight',16,48,75.,1e-9))
RATES=(20,10,5)


def build(p,nx,nr,J,kind):
    p.validate()
    a=3*p.eps/p.R;beta=p.F/(2*p.gas*p.T)
    ext=J*p.S/p.ksep+np.arcsinh(J/(2*p.jli))/beta
    model=pybamm.BaseModel(name='Canonical single-ion ASSB')
    x=pybamm.SpatialVariable('x_p',domain=['positive electrode'],coord_sys='cartesian')
    r=pybamm.SpatialVariable('r_p',domain=['positive particle'],coord_sys='spherical polar')
    theta=pybamm.Variable('theta',domain=['positive particle'],auxiliary_domains={'secondary':'positive electrode'})
    pe=pybamm.Variable('phi_e',domain=['positive electrode'])
    ps=pybamm.Variable('phi_s',domain=['positive electrode'])
    surface=pybamm.surf(theta)
    j=2*p.j0*pybamm.sinh(beta*(4.4-1.9*surface-ps+pe))
    v=pybamm.boundary_value(ps,'right')
    model.rhs={theta:pybamm.div(p.D*pybamm.grad(theta))}
    # Multiplication by L^2/k gives algebraic equations in voltage units.
    model.algebraic={pe:p.L**2*(pybamm.div(pybamm.grad(pe))-a*j/p.kcat),
                     ps:p.L**2*(pybamm.div(pybamm.grad(ps))+a*j/p.scat)}
    model.boundary_conditions={theta:{'left':(pybamm.Scalar(0),'Neumann'),'right':(j/(p.F*p.cmax*p.D),'Neumann')},
        pe:{'left':(pybamm.Scalar(-ext),'Dirichlet'),'right':(pybamm.Scalar(0),'Neumann')},
        ps:{'left':(pybamm.Scalar(0),'Neumann'),'right':(pybamm.Scalar(-J/p.scat),'Neumann')}}
    model.initial_conditions={theta:pybamm.Scalar(.8),pe:pybamm.Scalar(-ext),ps:pybamm.Scalar(4.4-1.9*.8-ext)}
    model.variables={'theta':theta,'phi_e':pe,'phi_s':ps,'Voltage':v,'Surface':surface,
                     'Reaction density':a*j,'Current error':pybamm.Integral(a*j,x)-J}
    model.events=[pybamm.Event('bulk lower',pybamm.min(theta)),pybamm.Event('bulk upper',1-pybamm.max(theta)),
                  pybamm.Event('surface lower',pybamm.min(surface)),pybamm.Event('surface upper',1-pybamm.max(surface))]
    if kind!='rest':model.events.append(pybamm.Event('voltage cutoff',p.high-v if kind=='charge' else v-p.low))
    geometry={'positive electrode':{x:{'min':0.,'max':p.L}},'positive particle':{r:{'min':0.,'max':p.R}}}
    domains=('positive electrode','positive particle')
    mesh=pybamm.Mesh(geometry,{d:pybamm.Uniform1DSubMesh for d in domains},{x:nx,r:nr})
    # Do not use Neumann BC to extrapolate surface concentration: its flux depends
    # on surface concentration itself. Independent linear centre extrapolation.
    method=pybamm.FiniteVolume(options={'extrapolation':{'order':{'value':'linear','gradient':'quadratic'},'use bcs':False}})
    disc=pybamm.Discretisation(mesh,{d:method for d in domains})
    return disc.process_model(model),mesh


def stage(p,nx,nr,rate,kind,step,rtol,previous=None):
    J=p.current_density(rate)*{'charge':-1,'rest':0,'discharge':1}[kind]
    model,mesh=build(p,nx,nr,J,kind)
    if previous is not None:model.set_initial_conditions_from(previous)
    solver=pybamm.IDAKLUSolver(rtol=rtol,atol=rtol*.01,root_tol=1e-10,options={'dt_max':step,'max_num_steps':100000})
    horizon=1800. if kind=='rest' else 2*rate*3600.
    sol=solver.solve(model,[0.,horizon])
    t=np.asarray(sol.t);end=float(t[-1])
    c=np.asarray(sol['theta'].entries);v=np.asarray(sol['Voltage'].entries).reshape(-1)
    surf=np.asarray(sol['Surface'].entries);reaction=np.asarray(sol['Reaction density'].entries)
    assert c.shape==(nr,nx,len(t)) and surf.shape==reaction.shape==(nx,len(t))
    assert len(t)>1 and np.all(np.diff(t)>0) and abs(t[0])<1e-12
    assert all(np.isfinite(z).all() for z in (c,v,surf,reaction))
    radial=np.asarray(mesh['positive particle'].edges);w=np.diff(radial**3);w/=w.sum()
    mean=np.einsum('r,rxt->t',w,c)/nx
    current_error=np.asarray(sol['Current error'].entries).reshape(-1)
    assert np.isfinite(current_error).all()
    # The scaled algebraic residual is independently evaluated from saved solver states.
    Y=np.asarray(sol.y)
    alg=max(float(np.max(np.abs(model.concatenated_algebraic.evaluate(t=float(ti),y=Y[:,i:i+1])))) for i,ti in enumerate(t))
    continuity=float(np.max(abs(c[:,:,0]-(.8 if previous is None else np.asarray(previous['theta'].entries)[:,:,-1]))))
    term=str(sol.termination)
    expected='rest_complete' if kind=='rest' else 'voltage'
    why='rest_complete' if kind=='rest' and abs(end-horizon)<1e-7 and term=='final time' else 'voltage' if kind!='rest' and 'voltage cutoff' in term and abs(v[-1]-(p.high if kind=='charge' else p.low))<=1e-5 else term
    xp=np.asarray(mesh['positive electrode'].nodes);probe=np.linspace(.125,.875,7)*p.L
    # Store the same 201 stage-local samples as the frozen reference protocol.
    ts=np.linspace(0,end,201)
    def interpolate(z):
        return np.interp(ts,t,z)
    sp=np.array([np.interp(probe,xp,surf[:,i]) for i in range(len(t))])
    jp=np.array([np.interp(probe,xp,reaction[:,i]) for i in range(len(t))])
    row=dict(rate=rate,stage=kind,termination=why,solver_termination=term,expected_termination=expected,
      end_s=end,capacity=abs(J)*p.A*end/(3.6*p.mass_g),current_density=J,start_mean=float(mean[0]),end_mean=float(mean[-1]),
      mass_residual=float(max(abs((mean-mean[0])*p.F*p.cmax*p.eps*p.L-J*t))),algebraic_residual=alg,
      current_residual=float(max(abs(current_error))),state_continuity_max=continuity,
      min_theta=float(min(c.min(),surf.min())),max_theta=float(max(c.max(),surf.max())),
      voltage_endpoint_error=0. if kind=='rest' else float(abs(v[-1]-(p.high if kind=='charge' else p.low))),
      time_s=ts.tolist(),voltage=interpolate(v).tolist(),mean_theta=interpolate(mean).tolist(),
      surface_probes=np.column_stack([interpolate(sp[:,i]) for i in range(7)]).tolist(),
      reaction_density_probes=np.column_stack([interpolate(jp[:,i]) for i in range(7)]).tolist(),
      native_samples=len(t))
    return row,sol


def healthy(row):
    return (row['termination']==row['expected_termination'] and row['mass_residual']<1e-5
            and row['algebraic_residual']<1e-8 and row['current_residual']<1e-8
            and row['state_continuity_max']<1e-10 and 0<row['min_theta']<=row['max_theta']<1)


def save(path,d):
    tmp=path.with_suffix('.part');tmp.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n');tmp.replace(path)


def run(path):
    p=Params();d=dict(scope='native symbolic single-ion PDE/DAE, PyBaMM FV and IDAKLU; matched synthetic sequential stages',environment=dict(python=platform.python_version(),pybamm=pybamm.__version__,pybammsolvers=importlib.metadata.version('pybammsolvers'),numpy=np.__version__),params=asdict(p),configs=CONFIGS,rows=[],pairs=[],errors=[],complete=False)
    save(path,d);lookup={}
    def add(row,name,label,nx,nr,step,tol):
        row.update(solver=name,config=label,mesh=[nx,nr],step=step,rtol=tol);d['rows'].append(row);lookup[name,label,row['rate'],row['stage']]=row;save(path,d)
    for label,nx,nr,step,tol in CONFIGS:
        for rate in RATES:
            prev=None
            for kind in ('charge','rest','discharge'):
                try:
                    row,prev=stage(p,nx,nr,rate,kind,step,tol,prev)
                    add(row,'PyBaMM',label,nx,nr,step,tol)
                    print('PyBaMM',label,rate,kind,row['termination'],healthy(row),flush=True)
                    if not healthy(row):raise RuntimeError('native physical/event gate failed')
                except Exception as e:
                    d['errors'].append(dict(solver='PyBaMM',config=label,rate=rate,stage=kind,error=repr(e)));save(path,d);return d
    for name,cls in [('FVM',Solver),('FEM',FEM)]:
        for rate in RATES:
            for row in cycle(cls(p,16,48),rate,150.,1e-8):add(row,name,'fine',16,48,150.,1e-8)
    for rate in RATES:
        for kind in ('charge','rest','discharge'):
            for label,a,b in [('spatial','coarse','fine'),('time','fine','tight')]:
                d['pairs'].append(dict(kind=label,rate=rate,stage=kind,**compare(lookup['PyBaMM',a,rate,kind],lookup['PyBaMM',b,rate,kind])))
            for name in ('FVM','FEM'):
                d['pairs'].append(dict(kind='cross_'+name,rate=rate,stage=kind,**compare(lookup['PyBaMM','tight',rate,kind],lookup[name,'fine',rate,kind])))
    d['physical_gate']=all(healthy(x) if x['solver']=='PyBaMM' else x['termination']==('rest_complete' if x['stage']=='rest' else 'voltage') and x['mass_residual']<1e-5 and x['algebraic_residual']<1e-8 and 0<x['min_theta']<=x['max_theta']<1 for x in d['rows'])
    d['comparison_gate']=all(x['max_voltage_mv']<=1 and x['capacity_delta_pct']<=.5 for x in d['pairs'])
    d['complete']=len(d['rows'])==45 and len(d['pairs'])==36
    save(path,d);return d


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);run(Path(parser.parse_args().out))
