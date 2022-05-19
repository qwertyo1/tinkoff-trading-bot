import asyncio

import pytest
from pytest_mock import MockFixture

from app.client import TinkoffClient
from app.strategies.interval.IntervalStrategy import IntervalStrategy
from app.strategies.interval.models import IntervalStrategyConfig


class TestOnHistoricalData:
    @pytest.mark.asyncio
    async def test_on_historical_data(
        self,
        mocker: MockFixture,
        mock_client: TinkoffClient,
        figi: str,
        test_config: IntervalStrategyConfig,
    ):
        mocker.patch("app.strategies.interval.IntervalStrategy.asyncio.sleep")
        strategy_instance = IntervalStrategy(figi=figi, config=test_config.dict())
        await strategy_instance.start()
        await asyncio.sleep(10000000)
        pass
