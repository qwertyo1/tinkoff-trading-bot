import datetime
from datetime import timedelta
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

import pytest
from pytest_mock import MockerFixture
from tinkoff.invest import GetAccountsResponse, Account, AsyncClient, Client
from tinkoff.invest.async_services import AsyncServices
from tinkoff.invest.caching.cache_settings import MarketDataCacheSettings
from tinkoff.invest.services import MarketDataCache, Services
from tinkoff.invest.utils import now

from app.client import TinkoffClient
from app.settings import settings
from app.strategies.interval.models import IntervalStrategyConfig


@pytest.fixture
def account_id():
    return "test_id"


@pytest.fixture
def figi():
    return "BBG000QDVR53"


@pytest.fixture
def accounts_response(account_id: str) -> GetAccountsResponse:
    return GetAccountsResponse(accounts=[Account(id=account_id)])


@pytest.fixture
def test_config() -> IntervalStrategyConfig:
    return IntervalStrategyConfig(
        interval_size=0.8,
        days_back_to_consider=1,
        corridor_update_interval=600,
        check_interval=60,
        stop_loss_percentage=0.1,
        quantity_limit=0,
    )


@pytest.fixture
def client() -> Services:
    with Client(settings.token) as client:
        yield client


class CandleHandler:
    def __init__(self, config: IntervalStrategyConfig):
        self.now = now()
        self.from_date = self.now - timedelta(days=15)
        self.candles = []
        self.config = config

    async def get_all_candles(self, **kwargs):
        if not self.candles:
            with Client(settings.token) as client:
                market_data_cache = MarketDataCache(
                    settings=MarketDataCacheSettings(base_cache_dir=Path("market_data_cache")),
                    services=client,
                )
                self.candles = list(
                    market_data_cache.get_all_candles(
                        figi=kwargs["figi"],
                        to=self.now,
                        from_=self.from_date,
                        interval=kwargs["interval"],
                    )
                )
        for candle in self.candles:
            if (
                self.from_date
                < candle.time
                < self.from_date + timedelta(days=self.config.days_back_to_consider)
            ):
                yield candle
        self.from_date += timedelta(seconds=self.config.corridor_update_interval)


@pytest.fixture
def mock_client(
    mocker: MockerFixture,
    accounts_response: GetAccountsResponse,
    client: Services,
    test_config: IntervalStrategyConfig,
) -> TinkoffClient:
    instance = AsyncMock()
    # accounts_response = AsyncMock()
    # accounts_response.accounts = AsyncMock(return_value=[AsyncMock().id(return_value=account_id)])
    # instance.get_accounts.return_value = AsyncMock()
    client_mock = mocker.patch("app.strategies.interval.IntervalStrategy.client")
    client_mock.get_accounts = AsyncMock(return_value=accounts_response)

    market_data_cache = MarketDataCache(
        settings=MarketDataCacheSettings(base_cache_dir=Path("market_data_cache")),
        services=client,
    )

    from_date = now() - timedelta(days=5)
    candles = []

    client_mock.get_all_candles = CandleHandler(test_config).get_all_candles

    return instance
