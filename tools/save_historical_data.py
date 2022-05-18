import logging
from datetime import timedelta, datetime, timezone
from pathlib import Path

from pydantic import BaseSettings
from tinkoff.invest import Client, CandleInterval
from tinkoff.invest.caching.cache_settings import MarketDataCacheSettings
from tinkoff.invest.services import MarketDataCache
from tinkoff.invest.utils import now

logging.basicConfig(format="%(asctime)s %(levelname)s:%(message)s", level=logging.DEBUG)


class Settings(BaseSettings):
    token: str

    class Config:
        env_file = ".env"


settings = Settings()


def save_historical_data(figi: str, days_back: int):
    with Client(settings.token) as client:
        market_data_cache = MarketDataCache(
            settings=MarketDataCacheSettings(base_cache_dir=Path("market_data_cache")),
            services=client,
        )
        list(
            market_data_cache.get_all_candles(
                figi=figi,
                from_=now() - timedelta(days=days_back),
                to=datetime.utcfromtimestamp(1652888940).replace(tzinfo=timezone.utc),
                interval=CandleInterval.CANDLE_INTERVAL_1_MIN,
            )
        )


if __name__ == "__main__":
    save_historical_data(figi="BBG000QDVR53", days_back=183)
