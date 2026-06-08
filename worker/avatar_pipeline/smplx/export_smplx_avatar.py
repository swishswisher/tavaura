import os
import torch
import smplx
import trimesh

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "models"
)

OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__),
    "output"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_PATH = os.path.join(
    OUTPUT_DIR,
    "smplx_female_neutral.obj"
)

model = smplx.create(
    MODEL_PATH,
    model_type="smplx",
    gender="female",
    use_face_contour=True,
    num_betas=10,
    ext="npz"
)

output = model()

vertices = output.vertices.detach().cpu().numpy().squeeze()
faces = model.faces

mesh = trimesh.Trimesh(
    vertices=vertices,
    faces=faces
)

mesh.export(OUTPUT_PATH)

print(f"Exported avatar to: {OUTPUT_PATH}")

