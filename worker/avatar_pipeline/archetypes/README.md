# Avatar Archetypes

This package defines curated commercial SMPL-X body archetypes for Tavaura.
The presets use calibrated high-impact beta controls to create visibly distinct
but believable body silhouettes.

These archetypes are not connected to runtime render jobs yet. They are a
foundation for later shopper matching, photo matching, and merchant-facing
avatar selection.

## Archetypes

- `slim`
- `athletic`
- `soft`
- `broad`
- `plus_size`
- `petite`
- `tall`

## Run

From inside `worker/`:

```powershell
python avatar_pipeline/archetypes/render_archetypes.py
python avatar_pipeline/archetypes/compare_archetypes.py
```

If your shell has not activated the worker virtual environment, use:

```powershell
.\.venv\Scripts\python.exe avatar_pipeline/archetypes/render_archetypes.py
.\.venv\Scripts\python.exe avatar_pipeline/archetypes/compare_archetypes.py
```

## Output

Renders and the comparison sheet are written to:

```text
avatar_pipeline/archetypes/output/
```

The comparison sheet is:

```text
avatar_pipeline/archetypes/output/archetype_comparison.png
```
