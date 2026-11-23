# v0.2 numerical verification and acceptance scope

This repository is **a feasibility prototype**, not a full reproduction of
Dessantis et al. (2024). No measured charge/discharge traces are distributed.

## 1. Dimensionful SSE inverse PINN

For uniform ionic conductivity in the electrolyte separator, the 1D
single-ion Ohmic equation gives

    phi(x) - phi(0) = -J * x / kappa

where `J` is geometric current density (A/m^2), `x` is physical distance (m)
and `kappa` is ionic conductivity (S/m). For normalized coordinate
`z=x/L`, the observed physical voltage is

    phi(z) - phi(0) = -J * L * z / kappa  [V].

The synthetic inverse demo first generates dimensional potential observations,
adds **relative** Gaussian voltage noise using a reference voltage scale
`J*L/kappa_prior`, and then normalizes voltages for neural optimization.
Consequently the normalized PDE and flux constraint are mathematically
unchanged by simultaneous scaling of the applied current or separator length.
This invariance is expected under the ideal constant-kappa Ohmic assumptions;
it does **not** mean that measured voltage is insensitive to J or L.

The demo is a constant-kappa toy inverse problem, not an end-to-end P2D PINN
and not an experimental inference engine. No calibrated instrument noise,
interfacial resistance, temperature dependence or uncertainty interval exists.

## 2. Refined cutoff integration

`ReducedP2D.simulate_stage` refines the crossing of the voltage or SoC cutoff
by bisection inside the final time step. It reuses the existing implicit
radial FVM update with the interfacial reaction flux frozen at the left side
of the step, identical to the coarse integrator.

This removes **time-grid quantization of the stopping time** but does not
remove its time-integration error or guarantee conservation beyond the original
discretization. Physical comparisons must run a time-step sensitivity study.

A deterministic synthetic voltage ramp regression test crosses the 4.2 V
limit at 60 s using a 120 s outer step, and checks that time, voltage,
concentration and integrated capacity agree with the known event.

## 3. Independent spherical diffusion analytical benchmark

For constant particle diffusivity and zero flux at the spherical surface,

    dc/dt = D*(1/r^2)*d/dr(r^2*dc/dr)

has the radial Neumann eigenmode solution

    c(r,t) = c_bar + A*sin(k*r)/(k*r)*exp(-D*k^2*t)

with `k*R = 4.493409457909064`, the first positive solution of
`tan(kR)=kR`. The benchmark compares numerical **shell average**
concentrations against exact spherical shell averages; it is not merely a
test of zero-flux mass conservation. The test checks refinement in both
space and time, using the source paper's particle diffusivity and radius.

Run:

    python -m pytest -q tests/test_analytic_benchmarks.py
    python -m pytest -q tests/test_numerical.py
    python -m pytest -q tests/test_pinn.py
    solid-pinn simulate --rates 20 10 5 --dt 300

## 4. Next required evidence for paper-quality claims

1. Obtain measured charge/discharge points and both actual OCV branches
   with provenance and permitted usage.
2. Reconcile phase volume fractions, current and SOC conventions, unknown
   Butler-Volmer exchange currents and interface contact resistance.
3. Add **independent full-P2D** solution using a matching PyBaMM custom model
   or FEM formulation. A standard liquid-electrolyte DFN is not equivalent
   to the project's single-ion solid-electrolyte boundary-value problem.
4. Test `nx`, `nr` and `dt` convergence for voltage RMSE, cut-off capacity,
   local reaction current and concentration.
5. Calibrate using C/20 only, freeze parameters, then predict C/10 and C/5.
6. Report reproducibility, timing, parameter recovery, identifiability and
   uncertainty across random seeds.

**Do not claim reproduction of the published Table 3 errors until the
independent experimental validation gates have passed.**
