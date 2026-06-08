from __future__ import annotations

from .archetype_definitions import ARCHETYPES, AvatarArchetype


def get_archetype(name: str) -> AvatarArchetype:
    key = name.strip().lower()
    try:
        return ARCHETYPES[key]
    except KeyError as exc:
        available = ", ".join(sorted(ARCHETYPES))
        raise KeyError(f"Unknown avatar archetype '{name}'. Available: {available}") from exc


def list_archetypes() -> list[AvatarArchetype]:
    return [ARCHETYPES[name] for name in sorted(ARCHETYPES)]
