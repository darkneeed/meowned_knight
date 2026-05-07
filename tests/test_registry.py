from __future__ import annotations

from app.core.registry import build_service_registry


def test_registry_uses_fixed_codes() -> None:
    registry = build_service_registry()
    assert sorted(registry) == [1, 2, 3, 4, 5, 6, 7]
    assert registry[1].name == "Firewall"
    assert registry[7].name == "TrafficGuard"

