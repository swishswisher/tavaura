# Beta Calibration

This isolated calibration layer probes individual SMPL-X beta indices and records
simple geometric measurements from the resulting meshes.

The goal is to identify which beta dimensions affect visible silhouette traits
such as shoulders, hips, verticality, body mass, waist taper, and leg proportion.
That lets future morphology tuning use measured beta behavior instead of blind
guessing.

This does not change runtime rendering, body estimation, APIs, frontend code,
textures, hair, or realism enhancement.

## Run

From inside `worker/`:

```powershell
python avatar_pipeline/beta_calibration/beta_probe.py
python avatar_pipeline/beta_calibration/compare_beta_probes.py
```

If your shell has not activated the worker virtual environment, use:

```powershell
.\.venv\Scripts\python.exe avatar_pipeline/beta_calibration/beta_probe.py
.\.venv\Scripts\python.exe avatar_pipeline/beta_calibration/compare_beta_probes.py
```

## Output

Probe renders and the comparison sheet are written to:

```text
avatar_pipeline/beta_calibration/output/
```

The comparison sheet is:

```text
avatar_pipeline/beta_calibration/output/beta_probe_comparison.png
```
