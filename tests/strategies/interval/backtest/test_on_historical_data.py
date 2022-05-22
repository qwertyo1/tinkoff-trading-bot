import asyncio

import pytest
from pytest_mock import MockFixture

from app.client import TinkoffClient
from app.strategies.interval.IntervalStrategy import IntervalStrategy
from app.strategies.interval.models import IntervalStrategyConfig
from app.utils.quotation import quotation_to_float
from tests.strategies.interval.backtest.conftest import NoMoreDataError, PortfolioHandler


class TestOnHistoricalData:
    @pytest.mark.asyncio
    async def test_on_historical_data(
        self,
        mocker: MockFixture,
        mock_client: TinkoffClient,
        portfolio_handler: PortfolioHandler,
        figi: str,
        test_config: IntervalStrategyConfig,
    ):
        mocker.patch("app.strategies.interval.IntervalStrategy.asyncio.sleep")
        mocker.patch("app.strategies.interval.IntervalStrategy.StatsHandler.handle_new_order")
        mocker.patch("app.strategies.interval.IntervalStrategy.IntervalStrategy.ensure_market_open")
        strategy_instance = IntervalStrategy(figi=figi, **test_config.dict())
        with pytest.raises(NoMoreDataError):
            await strategy_instance.start()
        positions = portfolio_handler.positions
        average_price = portfolio_handler.average_price
        resources = portfolio_handler.resources
        with open("./tests/strategies/interval/backtest/test_on_historical_data.txt", "w") as f:
            f.write(
                f"Positions in portfolio: {positions}\n"
                f"It's average price:     {quotation_to_float(average_price)}\n"
                f"Balance left:           {resources}"
            )
