import asyncio
import logging
from datetime import timedelta
from typing import List, Optional

import numpy as np
from tinkoff.invest import CandleInterval, HistoricCandle, AsyncClient
from tinkoff.invest.async_services import AsyncServices
from tinkoff.invest.grpc.orders_pb2 import (
    ORDER_DIRECTION_SELL,
    ORDER_DIRECTION_BUY,
    ORDER_TYPE_MARKET,
)
from tinkoff.invest.utils import now

from app.settings import settings
from app.strategies.Interval.models import IntervalStrategyConfig, Corridor
from app.strategies.base import BaseStrategy
from app.utils.portfolio import get_position, get_order
from app.utils.quotation import quotation_to_float

logger = logging.getLogger(__name__)


class IntervalStrategy(BaseStrategy):
    def __init__(self, figi: str, **kwargs):
        self.account_id = None
        self.corridor: Optional[Corridor] = None
        self.figi = figi
        self.config: IntervalStrategyConfig = IntervalStrategyConfig(**kwargs)

    async def get_historical_data(self, client: AsyncServices) -> List[HistoricCandle]:
        candles = []
        logger.debug(
            f"Start getting historical data for {self.config.days_back_to_consider} "
            f"days back from now. figi={self.figi}"
        )
        async for candle in client.get_all_candles(
            figi=self.figi,
            from_=now() - timedelta(days=self.config.days_back_to_consider),
            to=now(),
            interval=CandleInterval.CANDLE_INTERVAL_1_MIN,
        ):
            candles.append(candle)
        logger.debug(f"Found {len(candles)} candles. figi={self.figi}")
        return candles

    async def find_corridor(self, client: AsyncServices) -> None:
        candles = await self.get_historical_data(client=client)
        values = []
        for candle in candles:
            values.append(quotation_to_float(candle.close))
        lower_percentile = (1 - self.config.interval_size) / 2 * 100
        corridor = list(np.percentile(values, [lower_percentile, 100 - lower_percentile]))
        logger.info(
            f"Corridor: {corridor}. days_back_to_consider={self.config.days_back_to_consider} "
            f"figi={self.figi}"
        )
        self.corridor = Corridor(bottom=corridor[0], top=corridor[1])

    async def handle_corridor_crossing_top(self, last_price: float, corridor: Corridor, client:AsyncServices):
        logger.debug(
            f"Last price {last_price} is higher than top corridor border {corridor.top}. "
            f"figi={self.figi}"
        )
        positions = (
            await client.sandbox.get_sandbox_portfolio(account_id=self.account_id)
        ).positions
        position = get_position(positions, self.figi)
        if position is not None and quotation_to_float(position.quantity) > 0:
            quantity = quotation_to_float(position.quantity)
            quantity_to_sell = min(quantity, self.config.quantity_limit)
            logger.info(
                f"Selling {self.config.quantity_limit} shares. Last price={last_price} figi={self.figi}"
            )
            await client.sandbox.post_sandbox_order(
                figi=self.figi,
                direction=ORDER_DIRECTION_SELL,
                quantity=quantity_to_sell,
                order_type=ORDER_TYPE_MARKET,
                account_id=self.account_id,
            )

    async def handle_corridor_crossing_bottom(self, last_price: float, corridor: Corridor, client:AsyncServices):
        logger.debug(
            f"Last price {last_price} is lower than bottom corridor border {corridor.bottom}. "
            f"figi={self.figi}"
        )
        # TODO: check if we have enough money to buy
        # TODO: check the result of the order and track its status
        await client.sandbox.post_sandbox_order(
            figi=self.figi,
            direction=ORDER_DIRECTION_BUY,
            quantity=self.config.quantity_limit,
            order_type=ORDER_TYPE_MARKET,
            account_id=self.account_id,
        )

    async def corridor_update_cycle(self):
        while True:
            await asyncio.sleep(self.config.corridor_update_interval)
            async with AsyncClient(settings.token) as client:
                await self.find_corridor(client=client)

    async def get_last_price(self, client: AsyncServices) -> float:
        last_prices_response = await client.market_data.get_last_prices(figi=[self.figi])
        last_prices = last_prices_response.last_prices
        return quotation_to_float(last_prices.pop().price)

    async def main_cycle(self):
        while True:
            await asyncio.sleep(self.config.check_interval)
            async with AsyncClient(settings.token) as client:
                orders = await client.sandbox.get_sandbox_orders(account_id=self.account_id)
                if get_order(orders=orders.orders, figi=self.figi):
                    logger.info(f"There are orders in progress. Waiting. figi={self.figi}")
                    continue

                last_price = await self.get_last_price(client=client)

                if last_price >= self.corridor.top:
                    await self.handle_corridor_crossing_top(
                        last_price=last_price, corridor=self.corridor, client=client
                    )
                elif last_price <= self.corridor.bottom:
                    await self.handle_corridor_crossing_bottom(
                        last_price=last_price, corridor=self.corridor, client=client
                    )

    async def start(self):
        # TODO: handle sandbox flag
        async with AsyncClient(settings.token) as client:
            # self.account_id = (await self.client.users.get_accounts()).accounts.pop().id
            self.account_id = (await client.sandbox.get_sandbox_accounts()).accounts.pop().id
            await self.find_corridor(client=client)

        asyncio.create_task(self.corridor_update_cycle())
        asyncio.create_task(self.main_cycle())

    async def stop(self):
        pass
