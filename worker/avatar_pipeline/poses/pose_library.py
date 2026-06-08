from __future__ import annotations

from .pose_definitions import POSES, AvatarPose


def get_pose(name: str) -> AvatarPose:
    key = name.strip().lower()
    try:
        return POSES[key]
    except KeyError as exc:
        available = ", ".join(sorted(POSES))
        raise KeyError(f"Unknown avatar pose '{name}'. Available: {available}") from exc


def list_poses() -> list[AvatarPose]:
    return [POSES[name] for name in sorted(POSES)]
