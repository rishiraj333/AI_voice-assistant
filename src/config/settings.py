from pydantic_settings import BaseSettings, SettingsConfigDict

### Application settings

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    openai_api_key: str
    whisper_model_size: str = "base"
    accent_model_path: str = "accent_classification.hdf5"
    # API key for X-API-Key header auth
    api_key: str = "dev-key"
    # Redis URL; None means fall back to in-memory session store
    redis_url: str | None = None
    temp_audio_path: str = "Temp.mp3"

settings = Settings()
