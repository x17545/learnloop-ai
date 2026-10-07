from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LearnLoop API"
    app_version: str = "0.1.0"

    secret_key: str
    access_token_expire_minutes: int = 60
    
    openai_api_key: str
    openai_base_url: str
    openai_model: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()