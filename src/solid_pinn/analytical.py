"""Small-signal porous electrode benchmark, Fuller & Harb (2018), sec. 5.4.
Coordinate y=x/L starts at separator; the book starts at collector (z=1-y).
Positive j inserts Li and positive J discharges, as in SOLiD-PINN.
"""
from dataclasses import replace
import numpy as np
from .parameters import Parameters


def corrected_paper_parameters(p=None):
    """Correct Table 2 footnote transcription; preserve frozen v0.6 defaults."""
    return replace(p or Parameters(), sigma_cathode_s_m=0.17)


def linear_profile(y, nu, kr):
    """Return i_e/J and a*L*j/J for linear BV, constant U, no gradients.

    Equivalent to Fuller & Harb (5.36)-(5.37) after reversing x.
    Valid for positive conductivity ratio and 0 <= nu <= 50.
    """
    y = np.asarray(y, dtype=float)
    if not np.all(np.isfinite(y)) or np.any((y < 0) | (y > 1)):
        raise ValueError('y must be in [0,1]')
    if not np.isfinite(nu) or not 0 <= nu <= 50 or not np.isfinite(kr) or kr <= 0:
        raise ValueError('invalid dimensionless parameters')
    if nu < 1e-7:
        return 1-y, np.ones_like(y)
    s = np.sinh(nu)
    w = (kr + (np.sinh(nu*(1-y))-kr*np.sinh(nu*y))/s)/(1+kr)
    q = nu*(np.cosh(nu*(1-y))+kr*np.cosh(nu*y))/((1+kr)*s)
    return w, q


def dimensionless(p):
    g = p.exchange_current_cathode_a_m2*p.faraday_c_mol/(p.gas_constant_j_mol_k*p.temperature_k)
    k, sig = p.kappa_cathode_effective, p.sigma_cathode_s_m
    nu = np.sqrt(p.active_surface_area_m_inv*g*p.cathode_m**2*(1/k+1/sig))
    return float(nu), k/sig


def benchmark_cases():
    p = replace(corrected_paper_parameters(), exchange_current_cathode_a_m2=.0566011934)
    yield 'corrected_baseline', p
    # Synthetic stress cases, not fitted material parameters.
    g = p.exchange_current_cathode_a_m2*p.faraday_c_mol/(p.gas_constant_j_mol_k*p.temperature_k)
    for name, kr in [('ionic_limited',.1),('symmetric',1.),('electronic_limited',10.)]:
        k = p.active_surface_area_m_inv*g*p.cathode_m**2*(1+kr)/9
        yield name, replace(p,kappa_sse_s_m=k/p.cathode_ionic_phase_fraction**p.cathode_bruggeman_exponent,sigma_cathode_s_m=k/kr)


def benchmark(meshes=(8,16,32), amplitudes=(1e-3,)):
    """Compare nonlinear numerical solvers in the small-current linear limit.
    FVM reaction compared to exact cell averages, FEM to exact nodal values.
    Error normalized by absolute mean reaction, not local near-zero values.
    """
    from .numerical import ReducedP2D
    from .reference_fem import ReferenceFEM
    rows=[]
    for name,p in benchmark_cases():
        nu,kr=dimensionless(p); aL=p.active_surface_area_m_inv*p.cathode_m
        for n in meshes:
            faces=np.linspace(0,1,n+1); w,q=linear_profile(faces,nu,kr)
            for amp in amplitudes:
                for sign,stage in ((-1,'charge'),(1,'discharge')):
                    J=sign*amp*p.exchange_current_cathode_a_m2*aL; I=J*p.area_m2
                    fem=ReferenceFEM(p,n,3); fvm=ReducedP2D(p,n,3)
                    fe=fem.fields(np.full(n+1,.5),I,stage).reaction*aL/J
                    fv=fvm.solve_potentials(np.full(n,.5*p.max_solid_concentration_mol_m3),I,stage).reaction_current_a_m2*aL/J
                    for solver,actual,exact in (('FEM',fe,q),('FVM',fv,-n*np.diff(w))):
                        rows.append(dict(case=name,solver=solver,nx=n,stage=stage,amplitude=amp,nu=nu,kr=kr,max_reaction_error_pct=100*np.max(abs(actual-exact)),rmse_reaction_pct=100*np.sqrt(np.mean((actual-exact)**2))))
    return rows


def phase_volume_fractions(mass_fractions, densities, void_fraction=0.):
    """Convert mass fractions of solid constituents using independently supplied densities.
    Void fraction is total-volume fraction; no density defaults are inferred.
    Include binder in the supplied mass vector if present.
    """
    w,rho=np.asarray(mass_fractions,float),np.asarray(densities,float)
    if w.ndim!=1 or w.shape!=rho.shape or not len(w) or not np.all(np.isfinite(w)) or not np.all(np.isfinite(rho)) or np.any(w<0) or np.any(rho<=0) or not np.isclose(w.sum(),1) or not 0<=void_fraction<1:
        raise ValueError('invalid composition, density or void fraction')
    v=w/rho
    return (1-void_fraction)*v/v.sum()


def usable_soc(theta, theta_charged, theta_discharged):
    """Map cathode lithium site occupancy to usable SoC, without clipping.
    Endpoints must come from independent material/OCV evidence.
    """
    if not 0<=theta_charged<theta_discharged<=1:
        raise ValueError('invalid stoichiometric endpoints')
    return (theta_discharged-np.asarray(theta,float))/(theta_discharged-theta_charged)
