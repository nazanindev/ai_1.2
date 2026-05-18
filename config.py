from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    github_token: str = ""
    database_url: str = "sqlite:///./pulls.db"

    class Config:
        env_file = ".env"


settings = Settings()
