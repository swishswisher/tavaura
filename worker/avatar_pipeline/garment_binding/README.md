# Garment Binding Tests

This package validates a first simple garment-on-body binding layer for Tavaura.
It creates a structured fitted T-shirt archetype around the SMPL-X torso,
including a stable hem, high neckline, shoulder continuity, and cylindrical
sleeves, then renders it over selected archetypes and poses.

This is not cloth simulation. It does not add physics, textures, skin, hair,
frontend integration, API integration, or runtime garment fitting.

The purpose is to check:

- the shirt follows the torso
- the shirt scales across archetypes
- severe clipping is visible during validation
- pose changes do not cause catastrophic mesh failure
- semantic regions are available for future deformation constraints and
  collision handling
- structured apparel topology is available before realism, textures, wrinkles,
  or physics are introduced
- the generated shirt is anatomically fitted with region-specific body
  candidates and offsets, so it follows the torso without collapsing into the
  body
- pre-fit archetype debug views cover front, side, perspective, and wireframe
  outputs so topology can be inspected before fitting

## Run

From inside `worker/`:

```powershell
python avatar_pipeline/garment_binding/render_garment_binding_tests.py
python avatar_pipeline/garment_binding/compare_garment_binding_tests.py
python avatar_pipeline/garment_binding/render_garment_archetypes_debug.py
python avatar_pipeline/garment_binding/render_garment_regions_debug.py
```

If your shell has not activated the worker virtual environment, use:

```powershell
.\.venv\Scripts\python.exe avatar_pipeline/garment_binding/render_garment_binding_tests.py
.\.venv\Scripts\python.exe avatar_pipeline/garment_binding/compare_garment_binding_tests.py
.\.venv\Scripts\python.exe avatar_pipeline/garment_binding/render_garment_archetypes_debug.py
.\.venv\Scripts\python.exe avatar_pipeline/garment_binding/render_garment_regions_debug.py
```

## Output

Renders and the comparison sheet are written to:

```text
avatar_pipeline/garment_binding/output/
```

The refined comparison sheet is:

```text
avatar_pipeline/garment_binding/output/garment_structure_comparison.png
```

Semantic region debug renders are written to:

```text
avatar_pipeline/garment_binding/output/regions/
```

Structured archetype debug renders are written to:

```text
avatar_pipeline/garment_binding/output/archetypes/
```

Surface-fit debug renders are written to:

```text
avatar_pipeline/garment_binding/output/fitted/
```

The fitted debug folder includes body-only, pre-fit, post-fit, and wireframe
views for each tested archetype.
