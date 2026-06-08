# Pose Tests

This package validates stable SMPL-X pose variation on top of curated avatar
archetypes. It is a geometry-only layer used before garment alignment work.

Pose matters because garment fitting depends on predictable shoulders, torso,
hips, and limb placement. These tests confirm that commercial archetypes keep
believable silhouettes outside the neutral pose before cloth or garment logic is
introduced.

No cloth simulation, physics, textures, hair, frontend integration, or runtime
render-job integration is included here.

## Run

From inside `worker/`:

```powershell
python avatar_pipeline/poses/render_pose_tests.py
python avatar_pipeline/poses/compare_pose_tests.py
```

If your shell has not activated the worker virtual environment, use:

```powershell
.\.venv\Scripts\python.exe avatar_pipeline/poses/render_pose_tests.py
.\.venv\Scripts\python.exe avatar_pipeline/poses/compare_pose_tests.py
```

## Output

Pose renders and the comparison sheet are written to:

```text
avatar_pipeline/poses/output/
```

The comparison sheet is:

```text
avatar_pipeline/poses/output/pose_test_comparison.png
```
