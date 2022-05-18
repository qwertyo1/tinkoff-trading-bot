from pydantic import BaseSettings


class Settings(BaseSettings):
    token: str
    sandbox: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
