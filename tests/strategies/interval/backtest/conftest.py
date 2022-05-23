from datetime import timedelta
from pathlib import Path
from typing import List
from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture
from tinkoff.invest import (
    GetAccountsResponse,
    Account,
    Client,
    GetOrdersResponse,
    GetLastPricesResponse,
    LastPrice,
    PortfolioResponse,
    PortfolioPosition,
    Quotation,
    OrderDirection,
    MoneyValue,
)
from tinkoff.invest.caching.cache_settings import MarketDataCacheSettings
from tinkoff.invest.services import MarketDataCache, Services
from tinkoff.invest.utils import now

from app.client import TinkoffClient
from app.settings import settings
from app.strategies.interval.models import IntervalStrategyConfig
from app.utils.quotation import quotation_to_float


class NoMoreDataError(Exception):
    pass


@pytest.fixture
def account_id():
    return "test_id"


@pytest.fixture(scope="session")
def figi() -> str:
    return "BBG000QDVR53"


@pytest.fixture(scope="session")
def comission() -> float:
    return 0.003


@pytest.fixture
def accounts_response(account_id: str) -> GetAccountsResponse:
    return GetAccountsResponse(accounts=[Account(id=account_id)])


@pytest.fixture
def orders_response(account_id: str) -> GetOrdersResponse:
    return GetOrdersResponse(orders=[])


@pytest.fixture
def get_portfolio_response(account_id: str) -> GetOrdersResponse:
    return GetOrdersResponse(orders=[])


@pytest.fixture(scope="session")
def test_config() -> IntervalStrategyConfig:
    return IntervalStrategyConfig(
        interval_size=0.8,
        days_back_to_consider=7,
        check_interval=600,
        stop_loss_percentage=0.1,
        quantity_limit=10,
    )


@pytest.fixture
def client() -> Services:
    with Client(settings.token) as client:
        yield client


class CandleHandler:
    def __init__(self, config: IntervalStrategyConfig):
        self.now = now()
        self.from_date = self.now - timedelta(days=90)
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

        any_returned = False
        for candle in self.candles:
            if self.from_date < candle.time:
                if candle.time < self.from_date + timedelta(days=self.config.days_back_to_consider):
                    any_returned = True
                    yield candle
                else:
                    break

        if not any_returned:
            raise NoMoreDataError()
        self.from_date += timedelta(seconds=self.config.check_interval)

    async def get_last_prices(self, figi: List[str]) -> GetLastPricesResponse:
        for candle in self.candles:
            if candle.time >= self.from_date + timedelta(days=self.config.days_back_to_consider):
                return GetLastPricesResponse(
                    last_prices=[LastPrice(figi=figi[0], price=candle.close, time=candle.time)]
                )
        raise NoMoreDataError()


class PortfolioHandler:
    def __init__(self, figi: str, comission: float, candle_handler: CandleHandler):
        self.positions = 0
        self.resources = 0
        self.figi = figi
        self.comission = comission
        self.candle_handler = candle_handler
        self.average_price = MoneyValue(units=0, nano=0)

    async def get_portfolio(self, **kwargs) -> PortfolioResponse:
        return PortfolioResponse(
            positions=[
                PortfolioPosition(
                    figi=self.figi,
                    quantity=Quotation(units=self.positions, nano=0),
                    average_position_price=self.average_price,
                )
            ]
        )

    async def post_order(
        self, quantity: int = 0, direction: OrderDirection = OrderDirection(0), **kwargs
    ):
        last_price_quotation = (
            (await self.candle_handler.get_last_prices(figi=[self.figi])).last_prices[0].price
        )
        last_price = quotation_to_float(last_price_quotation)
        # TODO: Make it count average price respecting amount
        if direction == OrderDirection.ORDER_DIRECTION_BUY:
            self.positions += quantity
            self.resources -= quantity * last_price + (self.comission * quantity * last_price)
            self.average_price = MoneyValue(
                units=last_price_quotation.units, nano=last_price_quotation.nano
            )
        elif direction == OrderDirection.ORDER_DIRECTION_SELL:
            self.positions -= quantity
            self.resources += quantity * last_price - (self.comission * quantity * last_price)
            self.average_price = MoneyValue(units=0, nano=0)


@pytest.fixture(scope="session")
def candle_handler(test_config: IntervalStrategyConfig) -> CandleHandler:
    return CandleHandler(test_config)


@pytest.fixture(scope="session")
def portfolio_handler(
    figi: str, comission: float, candle_handler: CandleHandler
) -> PortfolioHandler:
    return PortfolioHandler(figi, comission, candle_handler)


@pytest.fixture
def mock_client(
    mocker: MockerFixture,
    accounts_response: GetAccountsResponse,
    orders_response: GetOrdersResponse,
    candle_handler: CandleHandler,
    portfolio_handler: PortfolioHandler,
    figi: str,
    client: Services,
    test_config: IntervalStrategyConfig,
) -> TinkoffClient:
    client_mock = mocker.patch("app.strategies.interval.IntervalStrategy.client")
    client_mock.get_accounts = AsyncMock(return_value=accounts_response)
    client_mock.get_orders = AsyncMock(return_value=orders_response)

    client_mock.get_all_candles = candle_handler.get_all_candles
    client_mock.get_last_prices = AsyncMock(side_effect=candle_handler.get_last_prices)

    client_mock.get_portfolio = AsyncMock(side_effect=portfolio_handler.get_portfolio)
    client_mock.post_order = AsyncMock(side_effect=portfolio_handler.post_order)

    return client_mock
