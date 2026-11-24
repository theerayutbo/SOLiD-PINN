"""Optional independent PyBaMM single-ion reduced P2D DAE.
Uses only shared Parameters/OCV, not the FVM potential or diffusion operators.
Requires PyBaMM; model must be verified by execution, not merely import.
"""
import numpy as np
from .parameters import Parameters
from .ocv import ocv_v


def solve_stage(p=None, stage="charge", rate=20, nx=12, nr=20,
                output_step=30., initial_soc=None, ocv_function=ocv_v):
    import pybamm as pb
    p = p or Parameters()
    if stage not in ("charge","discharge") or rate <= 0 or nx<2 or nr<3 or output_step<=0:
        raise ValueError("invalid stage or discretisation")
    s0 = p.initial_soc if initial_soc is None else float(initial_soc)
    if not 0.005 < s0 < .995:
        raise ValueError("initial SOC outside operating interval")
    J = p.current_a(rate)/p.area_m2 * (-1 if stage=="charge" else 1)
    L, R = p.cathode_m, p.particle_radius_m
    k, sig = p.kappa_cathode_effective, p.sigma_cathode_s_m
    beta = p.faraday_c_mol/(2*p.gas_constant_j_mol_k*p.temperature_k)
    left = -np.arcsinh(J/(2*p.exchange_current_lithium_a_m2))/beta-J*p.separator_m/p.kappa_sse_s_m
    m = pb.BaseModel(name="SOLiD-PINN independent single-ion reference")
    domain = "positive electrode"
    particle = "positive particle"
    aux = {"secondary":domain}
    x = pb.SpatialVariable("x_p",domain=domain,coord_sys="cartesian")
    r = pb.SpatialVariable("r_p",domain=particle,auxiliary_domains=aux,coord_sys="spherical polar")
    pe = pb.Variable("Electrolyte potential [V]",domain=domain)
    ps = pb.Variable("Solid potential [V]",domain=domain)
    c = pb.Variable("Lithium concentration fraction",domain=particle,auxiliary_domains=aux)
    surf = pb.surf(c)
    soc_s = pb.minimum(pb.maximum(1-surf,0),1)
    grid = np.linspace(0,1,2001)
    u = pb.Interpolant(grid,np.asarray(ocv_function(grid,stage),float),soc_s,interpolator="linear")
    j = -2*p.exchange_current_cathode_a_m2*pb.sinh(beta*(ps-pe-u))
    ie = -k*pb.grad(pe)
    iss = -sig*pb.grad(ps)
    a = p.active_surface_area_m_inv
    m.algebraic = {pe:L*(pb.div(ie)+a*j),ps:L*(pb.div(iss)-a*j)}
    D = p.particle_diffusivity_m2_s
    m.rhs = {c:D*pb.div(pb.grad(c))}
    S = pb.Scalar
    m.boundary_conditions = {
        pe:{"left":(S(left),"Dirichlet"),"right":(S(0),"Neumann")},
        ps:{"left":(S(0),"Neumann"),"right":(S(-J/sig),"Neumann")},
        c:{"left":(S(0),"Neumann"),"right":(j/(p.faraday_c_mol*D*p.max_solid_concentration_mol_m3),"Neumann")},
    }
    m.initial_conditions = {c:S(1-s0),pe:S(left),ps:S(float(ocv_function(s0,stage))+left)}
    v = pb.boundary_value(ps,"right")
    soc = 1-pb.Integral(pb.r_average(c),x)/L
    current_integral = a*pb.Integral(j,x)
    m.variables = {"Voltage [V]":v,"SOC":soc,"Lithium concentration fraction":c,
                   "Electrolyte potential [V]":pe,"Solid potential [V]":ps,
                   "Reaction current [A/m2]":j,"Integrated reaction current [A/m2]":current_integral}
    if stage=="charge":
        m.events = [pb.Event("Upper voltage",p.upper_cutoff_v-v),pb.Event("Upper SOC",.995-soc)]
    else:
        m.events = [pb.Event("Lower voltage",v-p.lower_cutoff_v),pb.Event("Lower SOC",soc-.005)]
    geom = {domain:{x:{"min":0,"max":L}},particle:{r:{"min":0,"max":R}}}
    mesh = pb.Mesh(geom,{domain:pb.Uniform1DSubMesh,particle:pb.Uniform1DSubMesh},{x:nx,r:nr})
    pb.Discretisation(mesh,{domain:pb.FiniteVolume(),particle:pb.FiniteVolume()}).process_model(m)
    end = rate*1.25*3600
    t = np.r_[np.arange(0,end,output_step),end]
    return pb.IDAKLUSolver(rtol=1e-8,atol=1e-9).solve(m,t)
