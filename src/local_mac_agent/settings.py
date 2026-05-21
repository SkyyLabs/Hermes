from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseModel):
    name: str = "LocalMacAgent"
    environment: str = "development"


class ModelSettings(BaseModel):
    provider: str = "ollama"
    model_name: str = "gemma3"
    base_url: str = "http://127.0.0.1:11434"
    local_only: bool = True


class SafetySettings(BaseModel):
    cloud_apis_enabled: bool = False
    require_confirmation_for_unknown_actions: bool = True


class RagSettings(BaseModel):
    enabled: bool = False
    resources_dir: str = "resources"


class MemorySettings(BaseModel):
    enabled: bool = False
    memory_dir: str = "memory"


class LoggingSettings(BaseModel):
    level: str = "INFO"
    jsonl_file: str = "logs/events.jsonl"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="LOCAL_MAC_AGENT_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    app: AppSettings = Field(default_factory=AppSettings)
    model: ModelSettings = Field(default_factory=ModelSettings)
    safety: SafetySettings = Field(default_factory=SafetySettings)
    rag: RagSettings = Field(default_factory=RagSettings)
    memory: MemorySettings = Field(default_factory=MemorySettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)


_CONFIG_MODELS = {
    "app": AppSettings,
    "model": ModelSettings,
    "safety": SafetySettings,
    "rag": RagSettings,
    "memory": MemorySettings,
    "logging": LoggingSettings,
}


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    content = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(content, dict):
        raise ValueError(f"Config file must contain a mapping: {path}")
    return content


def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        current = merged.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            merged[key] = _merge(current, value)
        else:
            merged[key] = value
    return merged


def load_settings(root: Path | None = None) -> Settings:
    """Load safe defaults, YAML config files, then environment overrides."""
    project_root = (root or Path.cwd()).resolve()
    config_dir = project_root / "configs"
    yaml_values: dict[str, Any] = {}
    for section, model_type in _CONFIG_MODELS.items():
        values = _read_yaml_mapping(config_dir / f"{section}.yaml")
        yaml_values[section] = model_type.model_validate(values).model_dump()

    env_values = Settings(_env_file=project_root / ".env").model_dump(exclude_unset=True)
    return Settings.model_validate(_merge(yaml_values, env_values))
