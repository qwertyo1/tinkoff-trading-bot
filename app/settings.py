import logging
from typing import Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    token: str
    account_id: Optional[str] = None
    sandbox: bool = True
    log_level = logging.DEBUG
    tinkoff_library_log_level = logging.INFO
    use_candle_history_cache = True

    class Config:
        env_file = ".env"


settings = Settings()
