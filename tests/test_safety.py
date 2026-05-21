import pytest

from local_mac_agent.safety import SafetyGuard


def test_classifies_known_and_unknown_actions() -> None:
    guard = SafetyGuard()

    assert guard.classify_action("read") == "safe"
    assert guard.classify_action("delete") == "requires_confirmation"
    assert guard.classify_action("export_credentials") == "blocked"
    assert guard.classify_action("future_action") == "requires_confirmation"


def test_confirmation_and_blocking_checks() -> None:
    guard = SafetyGuard()

    assert guard.assert_allowed("read") is True
    assert guard.assert_allowed("delete", confirmed=True) is True
    assert guard.requires_confirmation("future_action") is True
    assert guard.is_blocked("wipe_directory") is True
    with pytest.raises(PermissionError):
        guard.assert_allowed("delete")
    with pytest.raises(PermissionError):
        guard.assert_allowed("wipe_directory", confirmed=True)
