import asyncio

import pytest
from pytest_mock import MockFixture

from app.client import TinkoffClient
from app.strategies.interval.IntervalStrategy import IntervalStrategy
from app.strategies.interval.models import IntervalStrategyConfig
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
        strategy_instance = IntervalStrategy(figi=figi, **test_config.dict())
        with pytest.raises(NoMoreDataError):
            await strategy_instance.start()
        positions = portfolio_handler.positions
        breakpoint()
