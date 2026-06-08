# Pose Calibration

This package probes each SMPL-X `body_pose` index so we can identify which
indices control shoulders, elbows, hips, knees, spine, and other major joints.

It is calibration-only infrastructure. It does not add garment fitting, runtime
integration, frontend code, textures, skin, or hair.

## Run

From inside `worker/`:

```powershell
python avatar_pipeline/pose_calibration/pose_probe.py
python avatar_pipeline/pose_calibration/compare_pose_probes.py
```

If your shell has not activated the worker virtual environment, use:

```powershell
.\.venv\Scripts\python.exe avatar_pipeline/pose_calibration/pose_probe.py
.\.venv\Scripts\python.exe avatar_pipeline/pose_calibration/compare_pose_probes.py
```

## Output

Probe renders and the comparison sheet are written to:

```text
avatar_pipeline/pose_calibration/output/
```

The comparison sheet is:

```text
avatar_pipeline/pose_calibration/output/pose_probe_comparison.png
```
