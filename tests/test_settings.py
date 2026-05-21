from pathlib import Path

from local_mac_agent.settings import load_settings


def _write_config(root: Path, section: str, content: str) -> None:
    configs = root / "configs"
    configs.mkdir(exist_ok=True)
    (configs / f"{section}.yaml").write_text(content, encoding="utf-8")


def test_load_settings_uses_safe_defaults(tmp_path: Path) -> None:
    settings = load_settings(tmp_path)

    assert settings.app.name == "LocalMacAgent"
    assert settings.model.provider == "ollama"
    assert settings.model.model_name == "gemma3"
    assert settings.model.local_only is True
    assert settings.voice.wake_word == "hey_mycroft"
    assert settings.voice.sample_rate == 16000
    assert settings.voice.whisper_model == "tiny.en"
    assert settings.voice.utterance_silence_seconds == 0.45
    assert settings.safety.cloud_apis_enabled is False


def test_load_settings_reads_yaml_sections(tmp_path: Path) -> None:
    _write_config(tmp_path, "app", "name: Desktop Assistant\nenvironment: test\n")
    _write_config(tmp_path, "logging", "level: DEBUG\n")

    settings = load_settings(tmp_path)

    assert settings.app.name == "Desktop Assistant"
    assert settings.app.environment == "test"
    assert settings.logging.level == "DEBUG"


def test_environment_overrides_yaml(tmp_path: Path, monkeypatch) -> None:
    _write_config(tmp_path, "app", "name: YAML Name\n")
    monkeypatch.setenv("LOCAL_MAC_AGENT_APP__NAME", "Env Name")

    settings = load_settings(tmp_path)

    assert settings.app.name == "Env Name"
