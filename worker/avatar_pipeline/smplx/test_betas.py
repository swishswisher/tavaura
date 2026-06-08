import os
import numpy as np
import torch
import smplx
import trimesh
import pyrender
from PIL import Image

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "models")
OUTPUT_DIR = os.path.join(BASE_DIR, "output", "betas")
os.makedirs(OUTPUT_DIR, exist_ok=True)

BODY_PRESETS = {
    "neutral": [0.0] * 10,
    "slim": [-1.5, 0.3, 0.0, -0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "athletic": [0.5, -0.6, 0.7, 0.4, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0],
    "broad": [1.2, -0.2, 0.9, 0.8, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0],
    "soft": [1.0, 0.8, -0.3, 0.4, 0.7, 0.0, 0.0, 0.0, 0.0, 0.0],
}

def render_body(vertices, faces, output_path):
    mesh = trimesh.Trimesh(vertices, faces)
    render_mesh = pyrender.Mesh.from_trimesh(mesh)

    scene = pyrender.Scene(bg_color=[1, 1, 1, 0])
    scene.add(render_mesh)

    camera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0)
    camera_pose = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.15],
        [0.0, 0.0, 1.0, 3.8],
        [0.0, 0.0, 0.0, 1.0],
    ])

    scene.add(camera, pose=camera_pose)
    scene.add(pyrender.DirectionalLight(color=np.ones(3), intensity=3.0), pose=camera_pose)

    renderer = pyrender.OffscreenRenderer(viewport_width=512, viewport_height=1024)
    color, _ = renderer.render(scene)
    renderer.delete()

    Image.fromarray(color).save(output_path)

def main():
    model = smplx.create(
        MODEL_PATH,
        model_type="smplx",
        gender="female",
        use_face_contour=True,
        num_betas=10,
        ext="npz",
    )

    for name, beta_values in BODY_PRESETS.items():
        betas = torch.tensor([beta_values], dtype=torch.float32)
        output = model(betas=betas)
        vertices = output.vertices.detach().cpu().numpy().squeeze()
        output_path = os.path.join(OUTPUT_DIR, f"{name}.png")
        render_body(vertices, model.faces, output_path)
        print(f"Saved {name}: {output_path}")

if __name__ == "__main__":
    main()

    


