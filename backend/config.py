"""Flask configuration variables."""
from typing import Any
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

library_path = os.path.dirname(os.path.abspath(__file__))
class settingsModel(BaseSettings):
    # Whisper Settings
    SOUND_DEVICE: int = 0
    energy_threshold: int = 1000
    record_timeout: int = 2
    phrase_timeout: int = 3
    
    _enable_transcription: bool = True
    
    ENV: str = "development"
    LOGGING: bool = True

    model_config = SettingsConfigDict(
        env_file=(
            ".env",
            ".env.development"
        )
    )

Settings = settingsModel()
