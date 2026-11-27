# v0.10.0 Colab reproduction audit

## Provenance
Original uploaded JSON 76,808 bytes, SHA256 18960d403156e1f29f3512d1f0b5c350afda8d8e3249033bc102dbe039d453ec; Git blob 2082b7e78af4ddb7ef50e52db856c3303d2b31c5. Archived as [v0100_summary.json](v0100_summary.json); remote readback byte-exact against reconstructed file and original Git blob. Pinned source revision b41845ef4f8c4d148cbe2ddd1da0b55266b4124f. Three pinned source Git blob IDs verified against previous source identity; reported SHA256 metadata matches notebook manifest. No independent Colab stdout or runtime environment metadata in this JSON. Four targeted tests reported; separate GitHub Actions run 45863098492 passed Python 3.10, 3.12 and PINN jobs on PR #45 head 72e04c5c8c64816ab0ebf093ff0b646b88651416.

## Independent audit of reported results
All 12 distinct mesh/rate/stage keys, 101 finite strictly increasing time samples per trajectory, exact endpoint time and voltage (within 1e-9 V), and Q=qnom*t_end/(3600*rate denominator) agree. All sampled concentration bounds, algebraic residual and inventory checks satisfy proposed gates. All six common-time interpolated voltage and capacity deltas independently recalculated exactly as reported. Joint refinement only (4x12/300s to 8x24/150s); no separate convergence or independent FEM/PyBaMM/COMSOL verification.
| Rate | Stage | Fine capacity (mAh/g) | Max sampled delta (mV) | Capacity delta (%) |
|---|---|---:|---:|---:|
| C/20 | Charge |165.490818707|.133231123202|.002454865982|
| C/20 | Discharge |171.441805474|.133231123202|.002369654101|
| C/10 | Charge |163.034439428|.268462511256|.004983705053|
| C/10 | Discharge |168.985426196|.268462511256|.004808199003|
| C/5 | Charge |158.141097459|.552401697144|.010275830493|
| C/5 | Discharge |164.092084226|.552401697152|.009903165790|
Maximum reported mass residual 8.44011083245e-9 C/m2; mixed algebraic residual 1.94511073914e-13; sampled theta [.1358148363,.8378693742]. Capacity values agree with rounded prior local report (within 1e-6 mAh/g); no full local arrays available for independent trajectory-by-trajectory reproduction. C/20 to C/5 capacity drops 4.44117% charge, 4.28701% discharge. Independent starts, synthetic linear OCV, no aging, no real-cell calibration. Not a paired cycle or coulombic efficiency; qnom is a current convention, not capacity limit.

## Identifiability
Reported scaled Jacobian spectra (log parameters, 5 mV assumed IID noise, discharge only) at central step .0025:
| Singular value | C/20 | Combined C/20,C/10,C/5 |
|---:|---:|---:|
|1|17.010106441|76.881604893|
|2|.894288799|4.787550930|
|3|.013536739|.386348449|
|4|.002773108|.081341963|
|5|3.990065445e-7|.008800094|
|6|1.166498913e-11|.000623180|
At fixed current the separator Ohmic and Li-metal BV drops are both constant offsets; ksep and jli exactly confounded in this model. Near-null right singular vector has ksep .80757, jli -.58977; numerical floor is not an interpretable condition number. Combined condition 123369.8536; weakest direction dominated by scat (-.90058), with ksep .39978 and jli -.16337. Relative Jacobian step difference 2.93071e-6; smallest single-rate singular values unstable at numerical floor. SVD summaries are consistent with previous local report, not independently recomputed from raw Jacobian (not included). More samples contribute as well as additional rates. Local sensitivity, not global identifiability or parameter recovery. Do not infer all six parameters from terminal voltage alone.

## Decision
Joint numerical subgate passed. Next, independently implement axial/radial FEM and matched custom PyBaMM; separate spatial/time refinements, paired charge-discharge/rest, field exports and matched COMSOL setup. Full source equation audit still pending. Freeze synthetic material parameters and do not fit solver output to Dessantis capacity. After numerical verification, use designed pulse/rest and independent material/EIS evidence, multi-start profile likelihood and uncertainty, then compare supervised ML vs forward and inverse PINN. Keep historical Dessantis calibration/holdout and aging validation separate. CI passed, PR still draft; no merge performed in this audit.
