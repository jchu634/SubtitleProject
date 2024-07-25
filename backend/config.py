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

    encoder_target: str = 'cpu'
    decoder_target: str = 'aie'
    onnx_encoder_path: str = "models\\float-encoder.onnx"
    onnx_decoder_path: str = "models\\quant-decoder.onnx"
    
    ENV: str = "development"
    LOGGING: bool = True

    model_config = SettingsConfigDict(
        env_file=(
            ".env",
            ".env.development"
        )
    )

Settings = settingsModel()
