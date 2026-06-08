import os
import torch
import smplx
import trimesh
import pyrender
import numpy as np
from PIL import Image

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "models"
)

OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__),
    "output",
    "smplx_test.png"
)

model = smplx.create(
    MODEL_PATH,
    model_type='smplx',
    gender='female',
    use_face_contour=True,
    num_betas=10,
    ext='npz'
)

output = model()

vertices = output.vertices.detach().cpu().numpy().squeeze()
faces = model.faces

mesh = trimesh.Trimesh(vertices, faces)

render_mesh = pyrender.Mesh.from_trimesh(mesh)

scene = pyrender.Scene(bg_color=[1, 1, 1, 0])

scene.add(render_mesh)

camera = pyrender.PerspectiveCamera(
    yfov=np.pi / 3.0
)

camera_pose = np.array([
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 0.0, 0.0],
    [0.0, 0.0, 1.0, 3.5],
    [0.0, 0.0, 0.0, 1.0],
])

scene.add(camera, pose=camera_pose)

light = pyrender.DirectionalLight(
    color=np.ones(3),
    intensity=3.0
)

scene.add(light, pose=camera_pose)

renderer = pyrender.OffscreenRenderer(
    viewport_width=512,
    viewport_height=1024
)

color, _ = renderer.render(scene)

Image.fromarray(color).save(OUTPUT_PATH)

print(f"Saved render to: {OUTPUT_PATH}")

