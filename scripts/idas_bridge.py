"""Independent IDAS integration of the existing FV semi-discrete DAE."""
import json
from pathlib import Path
import numpy as np
import casadi as ca
from canonical_fv import Params, Solver
from verify_foundation import compare


def stage(s,c,rate,kind,rtol=1e-9):
    p=s.p;n,m=s.n,s.m;J=p.current_density(rate)*{'charge':-1,'rest':0,'discharge':1}[kind]
    x=ca.SX.sym('x',n*m);z=ca.SX.sym('z',n+1);h=ca.SX.sym('h')
    C=ca.reshape(x,m,n);q=z[:n];v=z[n]
    surf=C[-1,:].T+s.e*(C[-1,:]-C[-2,:]).T
    ode=ca.DM(s.L)@C+ca.DM(s.b)@q.T
    alg=ca.vertcat(ca.DM(s.K)@q+ca.asinh(q/(2*p.j0*s.a*s.dx))/s.beta+v-(4.4-1.9*surf),ca.sum1(q)-J)
    ext=J*p.S/p.ksep+np.arcsinh(J/(2*p.jli))/s.beta
    dae=dict(x=x,z=z,p=h,ode=h*ca.reshape(ode,n*m,1),alg=alg)
    opts=dict(abstol=rtol*.01,reltol=rtol,calc_ic=True,max_num_steps=10000)
    step=ca.integrator('step','idas',dae,0.,1.,opts)
    v0,q0,_,_=s.fields(c,J);x0=c.ravel();z0=np.r_[q0,v0+ext]
    def advance(xi,zi,dt):
        a=step(x0=xi,z0=zi,p=dt);return np.array(a['xf']).ravel(),np.array(a['zf']).ravel()
    def margin(xi,zi):
        a=xi.reshape(n,m);b=a[:,-1]+s.e*(a[:,-1]-a[:,-2]);V=zi[-1]-ext
        u=min(a.min(),1-a.max(),b.min(),1-b.max())
        return min(u,p.high-V if kind=='charge' else V-p.low) if kind!='rest' else u
    if margin(x0,z0)<=0:raise RuntimeError('invalid initial state')
    horizon=1800. if kind=='rest' else 2*rate*3600.;dt=horizon/40.;t=0.;xi=x0;zi=z0
    for _ in range(40):
        xx,zz=advance(xi,zi,dt)
        if margin(xx,zz)<=0:
            lo,hi=0.,dt
            for _ in range(32):
                mid=(lo+hi)/2;xm,zm=advance(xi,zi,mid)
                if margin(xm,zm)>0:lo=mid
                else:hi=mid
            t+=hi;break
        t+=dt;xi,zi=xx,zz
    grid=np.linspace(0.,1.,201)[1:].tolist()
    whole=ca.integrator('whole','idas',dae,0.,grid,opts)
    a=whole(x0=x0,z0=z0,p=t);xs=np.column_stack([x0,np.array(a['xf'])]).T.reshape(201,n,m);zs=np.column_stack([z0,np.array(a['zf'])]).T
    times=np.linspace(0,t,201);v=zs[:,-1]-ext;surfs=xs[:,:,-1]+s.e*(xs[:,:,-1]-xs[:,:,-2]);mean=(xs@s.w).mean(axis=1)
    why='rest_complete' if kind=='rest' and abs(t-horizon)<1e-6 else 'voltage' if kind!='rest' and abs(v[-1]-(p.high if kind=='charge' else p.low))<1e-6 else 'other'
    residual=zs[:,:n]@s.K.T+np.arcsinh(zs[:,:n]/(2*p.j0*s.a*s.dx))/s.beta+zs[:,-1,None]-(4.4-1.9*surfs)
    xp=(np.arange(n)+.5)*s.dx;probe=np.linspace(.125,.875,7)*p.L
    d=dict(stage=kind,rate=rate,termination=why,end_s=t,capacity=abs(J)*p.A*t/(3.6*p.mass_g),start_mean=float(mean[0]),end_mean=float(mean[-1]),mass_residual=float(max(abs((mean-mean[0])*p.F*p.cmax*p.eps*p.L-J*times))),algebraic_residual=float(max(np.max(abs(residual)),max(abs(zs[:,:n].sum(1)-J)))),min_theta=float(min(xs.min(),surfs.min())),max_theta=float(max(xs.max(),surfs.max())),time_s=times.tolist(),voltage=v.tolist(),mean_theta=mean.tolist(),surface_probes=[np.interp(probe,xp,u).tolist() for u in surfs],reaction_density_probes=[np.interp(probe,xp,u/s.dx).tolist() for u in zs[:,:n]])
    return d,xs[-1]


def run(reference):
    rows=[];pairs=[]
    for n,m,label in [(8,24,'time'),(16,48,'fine')]:
        s=Solver(nx=n,nr=m)
        for rate in (20,10,5):
            c=np.full((n,m),.8)
            for kind in ('charge','rest','discharge'):
                d,c=stage(s,c,rate,kind);d.update(mesh=[n,m],config=label);rows.append(d)
                ref=next(u for u in reference['rows'] if u['solver']=='FVM' and u['config']==label and u['rate']==rate and u['stage']==kind)
                pair=dict(config=label,rate=rate,stage=kind,**compare(d,ref));pairs.append(pair);print(pair,flush=True)
    return dict(scope='IDAS DAE integration on shared FV spatial matrices, no PyBaMM execution',casadi=ca.__version__,rows=rows,pairs=pairs,physical_gate=all(x['termination']==('rest_complete' if x['stage']=='rest' else 'voltage') and x['mass_residual']<1e-5 and x['algebraic_residual']<1e-8 and 0<x['min_theta']<=x['max_theta']<1 for x in rows),time_gate=all(x['max_voltage_mv']<=1 and x['capacity_delta_pct']<=.5 for x in pairs))

if __name__=='__main__':
    import sys
    Path(sys.argv[2]).write_text(json.dumps(run(json.loads(Path(sys.argv[1]).read_text())),indent=2,allow_nan=False)+'\n')
