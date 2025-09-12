from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "sqlite+aiosqlite:///data/cycling_coach.db"
    
    # File storage settings
    GPX_STORAGE_PATH: str = "data/gpx"
    
    # AI settings
    AI_MODEL: str = "deepseek/deepseek-r1"
    OPENROUTER_API_KEY: str = ""
    
    # Garmin settings
    GARMIN_USERNAME: str = ""
    GARMIN_PASSWORD: str = ""
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()