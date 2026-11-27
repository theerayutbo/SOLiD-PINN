# v0.10.1b — DAE integration and native PyBaMM verification

Merged foundation v0.10.1a: c291c83a4bb6f8f409f061d3f31b6d7c77449751. No parameter fit, no experimental data, no change to canonical equations. The previous FEM/FVM check shared scipy BDF. Here two distinct subgates are kept separate.

## A. Executed CasADi IDAS subgate
Local CasADi 3.7.2, IDAS integrator (SUNDIALS DAE solver). Same FV spatial matrices and algebraic inverse-BV relation; initial algebraic guess from FVM, but coupled time integration by IDAS. Root bracket and bisection on interval endpoints; reintegrate to found endpoint and evaluate 201 samples; no continuous-time guarantee of absence of intermediate crossing. Three rates x three sequential stages x two meshes (8x24 and 16x48) = 18 stages. Compare against uploaded v0.10.1a JSON SHA256 0c30e05c3aa473e589cbcf2807736b34f39eeedf3efc74dd0ca23ee924d2700b at same mesh and physical time. All 18 pass voltage <=1 mV, capacity <=.5%, sampled bounds, event and residual tests. All 12 mean transitions exact. 
|Metric|Maximum|
|---|---:|
|Voltage difference mV|3.730555730996343e-5|
|Capacity delta %|1.5853096613227535e-9|
|Endpoint time difference s|1.3210810720920563e-6|
|Surface occupancy difference|2.5889566712677947e-8|
|Reaction density RMSE A/m3|.0025654968559245604|
|Inventory residual C/m2|9.764335118234158e-9|
|Mixed algebraic residual|1.8869039664082266e-10|

Sampled occupancy [.1356283231446308,.8380558873771045]. Fine max voltage 3.154094541102381e-5 mV. Local source SHA256 775dbd9085d8c3343233651fc31203dfe3b5be92ecaf518d207b3c21edb7ce4e, Git blob 54d8135540f3bdab8ad53792b2f5467837ec9365. Local raw result SHA256 4e73585b739f4395a6e6b33bf72223a22c647baff684d6a9717dcad0dc3dd92b, not uploaded in full. IDAS and scipy BDF are different implementations in the BDF family, not independent integration method classes. This is **not** PyBaMM, independent spatial assembly or validation of real battery physics.

## B. Native PyBaMM benchmark (prepared, unexecuted locally)
Pin pybamm 25.12.1. Docs: https://docs.pybamm.org/en/v25.12.1/source/api/solvers/idaklu_solver.html and https://docs.pybamm.org/en/v25.12.1/_modules/pybamm/spatial_methods/finite_volume.html. Native symbolic PDE: particle theta in positive particle domain with secondary positive electrode; spherical diffusion, insertion flux gradient j/(F cmax D); separate cathode potentials with div(k grad phi_e)=a*j and div(sigma grad phi_s)=-a*j; nonlinear BV insertion j=2*j0*sinh(beta*(U-phi_s+phi_e)). Left electrolyte potential analytic Li BV and separator drop, other blocking/current BCs; terminal collector boundary value. No stock liquid DFN. Independent PyBaMM mesh and FV discretisation (linear surface extrapolation without BC feedback); IDAKLU sparse DAE solve. Stage-specific model and previous solution initialisation, verify full differential state continuity. Native sampled bounds, current/inventory closure, scaled algebraic residual, event and state handoff checked. No synthetic parameters adjusted to match references.
Protocol: 8x24/150s/1e-8; 16x48/150s/1e-8; 16x48/75s/1e-9. 27 native stages plus 18 fresh matched fine FEM/FVM stages, 36 comparisons. Gate all voltage <=1 mV, capacity <=.5%; physical checks and state continuity. Stop and preserve native errors; never substitute IDAS or FVM if native run fails. Stage-local 201-point linear interpolation from native samples; field probes diagnostic only. Spatial pair changes both axes; time pair changes step and tolerances together. Full source review and COMSOL still outstanding. Local installation failed (no package distribution available); native execution not claimed. CI smoke and Colab pending. No merge until results reviewed.
