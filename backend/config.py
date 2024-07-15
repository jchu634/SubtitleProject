"""Flask configuration variables."""
from typing import Any
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

library_path = os.path.dirname(os.path.abspath(__file__))
class settingsModel(BaseSettings):
    SOUND_DEVICE: int = 0
    ENV: str = "development"
    LOGGING: bool = True

    model_config = SettingsConfigDict(
        env_file=(
            ".env",
            ".env.development"
        )
    )

Settings = settingsModel()
