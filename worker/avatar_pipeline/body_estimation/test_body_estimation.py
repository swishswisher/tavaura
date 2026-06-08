from __future__ import annotations

import sys
from pathlib import Path


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from body_estimation.beta_mapper import (  # noqa: E402
    describe_profile_effect,
    estimate_betas_from_profile,
)
from body_estimation.body_inputs import BodyInputProfile  # noqa: E402


def test_neutral_empty_profile_returns_10_betas() -> None:
    betas = estimate_betas_from_profile(BodyInputProfile())
    assert len(betas) == 10
    assert betas == [0.0] * 10


def test_all_betas_are_clamped() -> None:
    profile = BodyInputProfile(
        height_cm=260.0,
        weight_kg=260.0,
        body_shape="broad",
        shoulder_width="broad",
        torso_length="long",
        hip_width="broad",
        build="strong",
    )
    betas = estimate_betas_from_profile(profile)
    assert len(betas) == 10
    assert all(-3.0 <= value <= 3.0 for value in betas)


def test_slim_profile_differs_from_broad_profile() -> None:
    slim = estimate_betas_from_profile(
        BodyInputProfile(body_shape="slim", shoulder_width="narrow", build="light")
    )
    broad = estimate_betas_from_profile(
        BodyInputProfile(body_shape="broad", shoulder_width="broad", build="strong")
    )
    assert slim != broad


def test_athletic_profile_differs_from_soft_profile() -> None:
    athletic = estimate_betas_from_profile(
        BodyInputProfile(body_shape="athletic", build="strong")
    )
    soft = estimate_betas_from_profile(
        BodyInputProfile(body_shape="soft", build="medium")
    )
    assert athletic != soft


def test_repeated_same_input_is_deterministic() -> None:
    profile = BodyInputProfile(
        height_cm=178.0,
        weight_kg=76.0,
        body_shape="athletic",
        shoulder_width="broad",
        torso_length="average",
        hip_width="average",
        build="strong",
    )
    assert estimate_betas_from_profile(profile) == estimate_betas_from_profile(profile)


def run_tests() -> None:
    tests = [
        test_neutral_empty_profile_returns_10_betas,
        test_all_betas_are_clamped,
        test_slim_profile_differs_from_broad_profile,
        test_athletic_profile_differs_from_soft_profile,
        test_repeated_same_input_is_deterministic,
    ]
    for test in tests:
        test()

    slim = BodyInputProfile(body_shape="slim", shoulder_width="narrow", build="light")
    athletic = BodyInputProfile(
        height_cm=178.0,
        weight_kg=76.0,
        body_shape="athletic",
        shoulder_width="broad",
        build="strong",
    )
    print("body estimation tests passed")
    print("slim:", estimate_betas_from_profile(slim), describe_profile_effect(slim))
    print(
        "athletic:",
        estimate_betas_from_profile(athletic),
        describe_profile_effect(athletic),
    )


if __name__ == "__main__":
    run_tests()
