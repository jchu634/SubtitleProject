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
    phrase_timeout: int = 5

    encoder_target: str = 'aie'
    decoder_target: str = 'cpu'
    onnx_encoder_path: str = "models\\quant-encoder.onnx"
    onnx_decoder_path: str = "models\\float-decoder.onnx"
    
    ENV: str = "development"
    LOGGING: bool = True

    model_config = SettingsConfigDict(
        env_file=(
            ".env",
            ".env.development"
        )
    )

Settings = settingsModel()
