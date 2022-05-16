from pydantic import BaseSettings


class Settings(BaseSettings):
    token: str

    class Config:
        env_file = ".env"


settings = Settings()
