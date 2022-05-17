import logging

import numpy as np
from datetime import timedelta
from typing import List

from tinkoff.invest import AsyncClient, CandleInterval, HistoricCandle
from tinkoff.invest.async_services import AsyncServices
from tinkoff.invest.utils import now

from app.strategies.Interval.models import IntervalStrategyConfig
from app.strategies.base import BaseStrategy

logger = logging.getLogger(__name__)


class IntervalStrategy(BaseStrategy):
    def __init__(self, client: AsyncServices, figi: str, **kwargs):
        self.client = client
        self.figi = figi
        self.config: IntervalStrategyConfig = IntervalStrategyConfig(**kwargs)

    async def get_historical_data(self) -> List[HistoricCandle]:
        candles = []
        async for candle in self.client.get_all_candles(
            figi=self.figi,
            from_=now() - timedelta(days=self.config.days_back_to_consider),
            to=now(),
            interval=CandleInterval.CANDLE_INTERVAL_1_MIN,
        ):
            candles.append(candle)
        return candles

    def find_corridor(self, candles: List[HistoricCandle]):
        values = []
        for candle in candles:
            values.append(float(f"{candle.close.units}.{candle.close.nano}"))
        lower_percentile = (1 - self.config.interval_size) / 2 * 100
        return np.percentile(values, [lower_percentile, 100 - lower_percentile])

    async def start(self):
        candles = await self.get_historical_data()
        corridor = self.find_corridor(candles)
        logger.info(f"Corridor: {corridor}")

    async def stop(self):
        pass
