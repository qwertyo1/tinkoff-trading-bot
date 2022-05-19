import asyncio
import logging
from datetime import timedelta
from typing import List, Optional

import numpy as np
from tinkoff.invest import CandleInterval, HistoricCandle
from tinkoff.invest.grpc.orders_pb2 import (
    ORDER_DIRECTION_SELL,
    ORDER_DIRECTION_BUY,
    ORDER_TYPE_MARKET,
)
from tinkoff.invest.utils import now

from app.client import client
from app.strategies.interval.models import IntervalStrategyConfig, Corridor
from app.strategies.base import BaseStrategy
from app.utils.portfolio import get_position, get_order
from app.utils.quotation import quotation_to_float

logger = logging.getLogger(__name__)

# TODO: Move client to constructor
class IntervalStrategy(BaseStrategy):
    def __init__(self, figi: str, **kwargs):
        self.account_id = None
        self.corridor: Optional[Corridor] = None
        self.figi = figi
        self.config: IntervalStrategyConfig = IntervalStrategyConfig(**kwargs)

    async def get_historical_data(self) -> List[HistoricCandle]:
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

    async def update_corridor(self) -> None:
        candles = await self.get_historical_data()
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
        breakpoint()

    async def get_position_quantity(self) -> int:
        positions = (await client.get_portfolio(account_id=self.account_id)).positions
        position = get_position(positions, self.figi)
        if position is None:
            return 0
        return int(quotation_to_float(position.quantity))

    async def handle_corridor_crossing_top(self, last_price: float, corridor: Corridor):
        logger.debug(
            f"Last price {last_price} is higher than top corridor border {corridor.top}. "
            f"figi={self.figi}"
        )

        position_quantity = await self.get_position_quantity()
        if position_quantity > 0:
            quantity_to_sell = min(position_quantity, self.config.quantity_limit)
            logger.info(
                f"Selling {quantity_to_sell} shares. Last price={last_price} figi={self.figi}"
            )
            await client.post_order(
                figi=self.figi,
                direction=ORDER_DIRECTION_SELL,
                quantity=quantity_to_sell,
                order_type=ORDER_TYPE_MARKET,
                account_id=self.account_id,
            )

    async def handle_corridor_crossing_bottom(self, last_price: float, corridor: Corridor):
        logger.debug(
            f"Last price {last_price} is lower than bottom corridor border {corridor.bottom}. "
            f"figi={self.figi}"
        )
        position_quantity = await self.get_position_quantity()
        if position_quantity < self.config.quantity_limit:
            quantity_to_buy = self.config.quantity_limit - position_quantity
            logger.info(
                f"Buying {quantity_to_buy} shares. Last price={last_price} figi={self.figi}"
            )
            # TODO: check if we have enough money to buy
            # TODO: check the result of the order and track its status
            await client.post_order(
                figi=self.figi,
                direction=ORDER_DIRECTION_BUY,
                quantity=quantity_to_buy,
                order_type=ORDER_TYPE_MARKET,
                account_id=self.account_id,
            )

    async def corridor_update_cycle(self):
        while True:
            await asyncio.sleep(self.config.corridor_update_interval)
            await self.update_corridor()

    async def get_last_price(self) -> float:
        last_prices_response = await client.get_last_prices(figi=[self.figi])
        last_prices = last_prices_response.last_prices
        return quotation_to_float(last_prices.pop().price)

    async def main_cycle(self):
        while True:
            await asyncio.sleep(self.config.check_interval)

            orders = await client.get_orders(account_id=self.account_id)
            if get_order(orders=orders.orders, figi=self.figi):
                logger.info(f"There are orders in progress. Waiting. figi={self.figi}")
                continue

            last_price = await self.get_last_price()
            logger.debug(f"Last price: {last_price}, figi={self.figi}")

            # TODO: check if our position price should trigger stop loss

            if last_price >= self.corridor.top:
                await self.handle_corridor_crossing_top(
                    last_price=last_price, corridor=self.corridor
                )
            elif last_price <= self.corridor.bottom:
                await self.handle_corridor_crossing_bottom(
                    last_price=last_price, corridor=self.corridor
                )

    async def start(self):
        self.account_id = (await client.get_accounts()).accounts.pop().id
        await self.update_corridor()

        asyncio.create_task(self.corridor_update_cycle())
        asyncio.create_task(self.main_cycle())

    async def stop(self):
        pass
