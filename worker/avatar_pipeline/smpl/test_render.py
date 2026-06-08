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
    "smpl_test.png"
)

# Load SMPL model
model = smplx.create(
    MODEL_PATH,
    model_type='smpl',
    gender='female',
    ext='pkl'
)

# Generate neutral body
output = model()

vertices = output.vertices.detach().cpu().numpy().squeeze()
faces = model.faces

# Create trimesh
mesh = trimesh.Trimesh(vertices, faces)

# Convert to pyrender mesh
render_mesh = pyrender.Mesh.from_trimesh(mesh)

# Create scene
scene = pyrender.Scene(bg_color=[1, 1, 1, 0])

scene.add(render_mesh)

# Camera
camera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0)

camera_pose = np.array([
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 0.0, 0.0],
    [0.0, 0.0, 1.0, 3.0],
    [0.0, 0.0, 0.0, 1.0],
])

scene.add(camera, pose=camera_pose)

# Light
light = pyrender.DirectionalLight(
    color=np.ones(3),
    intensity=3.0
)

scene.add(light, pose=camera_pose)

# Render
renderer = pyrender.OffscreenRenderer(
    viewport_width=512,
    viewport_height=1024
)

color, _ = renderer.render(scene)

# Save image
Image.fromarray(color).save(OUTPUT_PATH)

print(f"Saved render to: {OUTPUT_PATH}")