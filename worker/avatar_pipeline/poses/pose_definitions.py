from __future__ import annotations

from dataclasses import dataclass


BODY_POSE_SIZE = 63
BODY_JOINT_COUNT = 21


@dataclass(frozen=True)
class AvatarPose:
    name: str
    description: str
    body_pose: list[float]


BODY_JOINTS = {
    "left_hip": 0,
    "right_hip": 1,
    "spine1": 2,
    "left_knee": 3,
    "right_knee": 4,
    "spine2": 5,
    "left_ankle": 6,
    "right_ankle": 7,
    "spine3": 8,
    "left_foot": 9,
    "right_foot": 10,
    "neck": 11,
    "left_collar": 12,
    "right_collar": 13,
    "head": 14,
    "left_shoulder": 15,
    "right_shoulder": 16,
    "left_elbow": 17,
    "right_elbow": 18,
    "left_wrist": 19,
    "right_wrist": 20,
}


def create_pose(
    *,
    name: str,
    description: str,
    rotations: dict[str, tuple[float, float, float]],
) -> AvatarPose:
    body_pose = [0.0] * BODY_POSE_SIZE
    for joint_name, rotation in rotations.items():
        joint_index = BODY_JOINTS[joint_name]
        start = joint_index * 3
        body_pose[start : start + 3] = [round(value, 4) for value in rotation]

    return AvatarPose(
        name=name,
        description=description,
        body_pose=body_pose,
    )


POSES: dict[str, AvatarPose] = {
    "t_pose": create_pose(
        name="t_pose",
        description="Neutral SMPL-X body pose for baseline garment alignment checks.",
        rotations={},
    ),
    "relaxed": create_pose(
        name="relaxed",
        description="Subtle relaxed stance with mild arm drop and small elbow bend.",
        rotations={
            "spine1": (0.015, 0.0, 0.0),
            "spine2": (-0.015, 0.0, 0.0),
            "left_shoulder": (0.10, 0.0, 0.18),
            "right_shoulder": (0.10, 0.0, -0.18),
            "left_elbow": (0.18, 0.0, 0.04),
            "right_elbow": (0.18, 0.0, -0.04),
            "left_wrist": (0.04, 0.0, 0.02),
            "right_wrist": (0.04, 0.0, -0.02),
        },
    ),
    "hands_on_hips": create_pose(
        name="hands_on_hips",
        description="Controlled hands-near-hips stance for shoulder and torso validation.",
        rotations={
            "spine3": (0.02, 0.0, 0.0),
            "left_shoulder": (0.28, -0.08, 0.42),
            "right_shoulder": (0.28, 0.08, -0.42),
            "left_elbow": (0.72, 0.0, -0.26),
            "right_elbow": (0.72, 0.0, 0.26),
            "left_wrist": (0.10, 0.0, -0.10),
            "right_wrist": (0.10, 0.0, 0.10),
        },
    ),
    "slight_walk": create_pose(
        name="slight_walk",
        description="Small walking offset with stable torso and modest leg separation.",
        rotations={
            "left_hip": (-0.12, 0.03, 0.04),
            "right_hip": (0.10, -0.02, -0.04),
            "left_knee": (0.18, 0.0, 0.0),
            "right_knee": (0.05, 0.0, 0.0),
            "left_ankle": (-0.05, 0.0, 0.0),
            "right_ankle": (0.04, 0.0, 0.0),
            "spine1": (0.0, 0.02, 0.02),
            "spine2": (0.0, -0.01, -0.01),
            "left_shoulder": (0.06, 0.0, 0.10),
            "right_shoulder": (0.10, 0.0, -0.16),
            "left_elbow": (0.12, 0.0, 0.02),
            "right_elbow": (0.16, 0.0, -0.02),
        },
    ),
    "one_leg_shift": create_pose(
        name="one_leg_shift",
        description="Subtle weight shift to one leg while preserving fitting stability.",
        rotations={
            "left_hip": (0.02, 0.0, 0.08),
            "right_hip": (-0.04, 0.0, -0.12),
            "left_knee": (0.04, 0.0, 0.0),
            "right_knee": (0.12, 0.0, 0.0),
            "spine1": (0.0, 0.0, -0.03),
            "spine2": (0.0, 0.0, 0.02),
            "left_shoulder": (0.08, 0.0, 0.14),
            "right_shoulder": (0.08, 0.0, -0.14),
            "left_elbow": (0.14, 0.0, 0.02),
            "right_elbow": (0.14, 0.0, -0.02),
        },
    ),
}
