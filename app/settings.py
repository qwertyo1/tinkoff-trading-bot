from typing import Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    token: str
    account_id: Optional[str] = None
    sandbox: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
