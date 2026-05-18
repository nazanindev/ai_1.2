from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    github_token: str = ""
    github_owner: str = ""
    github_repo: str = ""
    database_url: str = "sqlite:///./github_metrics.db"


settings = Settings()
