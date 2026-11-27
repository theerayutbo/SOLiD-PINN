# v0.10.1a: Independent FEM/FVM verification

Base: merged v0.10.0 (594f1c86efed95fcc502fd12c567038b16d5ffa8). Freeze synthetic geometry, material parameters, linear OCV and symmetric BV. No Dessantis data or fit. FEM independently assembles P1 Galerkin axial/radial mass and stiffness matrices by three-point Gauss quadrature, axial reaction source mass-lumped, radial mass consistent; eliminates axial potentials via separate stiffness solves with electrolyte reference at x=0 and solid reference at x=L. FVM uses conservative shells and centroid extrapolation. Both share the physical model, nonlinear reaction solve formulation and SciPy BDF integrator. Independent spatial discretization, not an independent time integrator or full P2D verification.

Start at uniform theta=.8 for each rate; charge to 4.15 V, rest 1800 s, discharge to 2.8 V; pass full final concentration array to next stage. No resetting SOC or capacity-derived endpoints. One sequence per rate/mesh/solver, not stabilized cycling or aging. Discharge can exceed charge because final occupancy exceeds initial occupancy; do not interpret ratio as steady-cycle CE. qnom=150 mAh/g defines current, not a capacity ceiling.

Configurations (axial x radial, max step s, rtol): coarse 4x12/300/1e-7; axial 8x12/300/1e-7; radial 8x24/300/1e-7; time 8x24/150/1e-8; fine 16x48/150/1e-8. atol=rtol*.01. Two solvers, three rates, three stages, five configs: 90 stages, 117 comparisons (72 refinement,45 cross-solver). Compare on 201 common physical-time points within overlapping intervals, using linear interpolation of saved traces. No time stretching/extrapolation. Keep endpoint and capacity differences. Seven interior axial probes (12.5–87.5% of cathode): surface occupancy and volumetric reaction density A/m3. Sampled diagnostic errors, not continuous or full-field guarantees.

## Executed CPU evidence
Pinned source c488e2d7d20f57f2de99ca1ecb1f886bcd95680a. NumPy 2.3.5, SciPy 1.17.0. Four new tests passed (2.37s). All 90 stages reached intended voltage/rest event; sampled physical gate and all 60 mean-state transitions pass. Max mass residual 8.58563e-8 C/m2, mixed algebraic residual 4.61853e-13, sampled theta [.13544181,.83824240]. All nine fine cross-solver comparisons pass <=1 mV sampled voltage and <=.5% capacity. Earlier coarse/axial comparisons fail voltage criterion; not all 117 pass. Last joint spatial refinement and temporal refinement comparisons all meet the two tolerances (18 each).

|Rate|FVM charge|FEM charge|FVM discharge|FEM discharge|
|---|---:|---:|---:|---:|
|C/20|165.491777917|165.492660134|173.613016878|173.614781312|
|C/10|163.036357850|163.038122284|168.702176743|168.705705611|
|C/5|158.144934302|158.148463170|158.919329647|158.926387384|

mAh/g; synthetic rate capability, not real-cell fade.

|Cross config|Max voltage mV|Max capacity %|Max surface theta|Max reaction RMSE A/m3|
|---|---:|---:|---:|---:|
|coarse|1.812797577|.072916462|.001285297|312.293341|
|axial|2.295780837|.019936391|.001568352|175.469397|
|radial|.899817321|.017917136|.000713879|119.723135|
|time|.900067460|.017917135|.000714082|119.730323|
|fine|.269283199|.004440884|.000198198|29.557305|

Fine max endpoint difference .846928483 s. Within-solver maxima:

|Change|max voltage mV|max capacity %|
|---|---:|---:|
|coarse to axial|.930240349|.061904609|
|axial to radial|2.040329796|.041478280|
|radial to time|.000292964|9.95870e-11|
|time to fine|.854842381|.008649348|

Initial radial change matters especially in rest. Fine gate passes but last spatial pair changes both axes; separate fine refinements and better sampling near switching advisable. Temporal change includes max step and tolerance together. No independent time integrator. Probe checks not full radial or phase-potential comparisons. Next matched custom PyBaMM single-ion implementation and COMSOL with same equations, material parameters, sign, IC/BC, events and state transfer. Export field data and preserve switch event sides. Full primary-source equation audit, material parameter evidence, ML/PINN and real-cell validation pending. Notebook exports full traces; local aggregate only recorded here. Colab and CI pending; no merge.
