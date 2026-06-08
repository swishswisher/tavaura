# Profile Render Test

This isolated test renders SMPL-X bodies from parameter-only `BodyInputProfile`
presets. It is for visual validation that MVP body estimation changes avatar
morphology before connecting the mapper to runtime render jobs.

It does not add APIs, frontend integration, photo estimation, textures, skin, hair,
or realism enhancement.

## Run

From inside `worker/`:

```powershell
python avatar_pipeline/profile_render_test/render_profiles.py
python avatar_pipeline/profile_render_test/compare_profiles.py
```

Amplified morphology validation:

```powershell
python avatar_pipeline/profile_render_test/render_amplified_profiles.py
python avatar_pipeline/profile_render_test/compare_amplified_profiles.py
python avatar_pipeline/profile_render_test/compare_original_vs_amplified.py
```

## Output

Individual profile renders are written to:

```text
avatar_pipeline/profile_render_test/output/
```

The comparison sheet is written to:

```text
avatar_pipeline/profile_render_test/output/profiles_comparison.png
```

Amplified renders and comparisons are written to:

```text
avatar_pipeline/profile_render_test/output_amplified/
```
