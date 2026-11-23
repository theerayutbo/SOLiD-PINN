# Experimental data provenance

**No experimental raw data from Dessantis et al. (2024) is bundled.**
The paper states "Data will be made available on request" (page 7).
Please request the original charge/discharge traces, OCV charge/discharge
points and material properties from its corresponding author.

Recommended file layout after receiving permission to redistribute:
- `data/experimental/C20.csv` : `time_h,voltage_v,stage`
- `data/experimental/C10.csv` : same schema
- `data/experimental/C5.csv` : same schema
- `data/experimental/ocv_charge.csv` : `soc,voltage_v`
- `data/experimental/ocv_discharge.csv` : `soc,voltage_v`

If extracting from PDF figures, label every point as digitised data and
record uncertainty, axes calibration, extraction method, and source figure.

Never use the illustrative functions in `src/solid_pinn/ocv.py` as if they
were digitized measurements. They are invented placeholders for code tests.
