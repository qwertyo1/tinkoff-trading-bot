import asyncio
import logging
from datetime import timedelta
from typing import List, Optional
from uuid import uuid4

import numpy as np
from tinkoff.invest import CandleInterval, HistoricCandle, AioRequestError
from tinkoff.invest.grpc.orders_pb2 import (
    ORDER_DIRECTION_SELL,
    ORDER_DIRECTION_BUY,
    ORDER_TYPE_MARKET,
)
from tinkoff.invest.utils import now

from app.client import client
from app.settings import settings
from app.stats.handler import StatsHandler
from app.strategies.interval.models import IntervalStrategyConfig, Corridor
from app.strategies.base import BaseStrategy
from app.strategies.models import StrategyName
from app.utils.portfolio import get_position, get_order
from app.utils.quotation import quotation_to_float

logger = logging.getLogger(__name__)


class IntervalStrategy(BaseStrategy):
    """
    Interval strategy.

    Main strategy logic is to buy at the lowest price and sell at the highest price of the
    calculated interval.

    Interval is calculated by taking interval_size percents of the last prices
    for the last days_back_to_consider days. By default, it's set to 80 percents which means
    that the interval is from 10th to 90th percentile.
    """

    def __init__(self, figi: str, **kwargs):
        self.account_id = settings.account_id
        self.corridor: Optional[Corridor] = None
        self.figi = figi
        self.config: IntervalStrategyConfig = IntervalStrategyConfig(**kwargs)
        self.stats_handler = StatsHandler(StrategyName.INTERVAL, client)

    async def get_historical_data(self) -> List[HistoricCandle]:
        """
        Gets historical data for the instrument. Returns list of candles.
        Requests all the 1-min candles from days_back_to_consider days back to now.

        :return: list of HistoricCandle
        """
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
        """
        Gets historical data and calculates new corridor. Stores it in the class.
        """
        candles = await self.get_historical_data()
        if len(candles) == 0:
            return
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

    async def get_position_quantity(self) -> int:
        """
        Get quantity of the instrument in the position.
        :return: int - quantity
        """
        positions = (await client.get_portfolio(account_id=self.account_id)).positions
        position = get_position(positions, self.figi)
        if position is None:
            return 0
        return int(quotation_to_float(position.quantity))

    async def handle_corridor_crossing_top(self, last_price: float) -> None:
        """
        This method is called when last price is higher than top corridor border.
        Check how many shares we already have and sell them.

        :param last_price: last price of the instrument
        """
        position_quantity = await self.get_position_quantity()
        if position_quantity > 0:
            logger.info(
                f"Selling {position_quantity} shares. Last price={last_price} figi={self.figi}"
            )
            try:
                posted_order = await client.post_order(
                    order_id=str(uuid4()),
                    figi=self.figi,
                    direction=ORDER_DIRECTION_SELL,
                    quantity=position_quantity,
                    order_type=ORDER_TYPE_MARKET,
                    account_id=self.account_id,
                )
            except Exception as e:
                logger.error(f"Failed to post sell order. figi={self.figi}. {e}")
                return
            asyncio.create_task(
                self.stats_handler.handle_new_order(
                    order_id=posted_order.order_id, account_id=self.account_id
                )
            )

    async def handle_corridor_crossing_bottom(self, last_price: float) -> None:
        """
        This method is called when last price is lower than bottom corridor border.
        Check how many shares we already have and buy more until the quantity_limit is reached.

        :param last_price: last price of the instrument
        """
        position_quantity = await self.get_position_quantity()
        if position_quantity < self.config.quantity_limit:
            quantity_to_buy = self.config.quantity_limit - position_quantity
            logger.info(
                f"Buying {quantity_to_buy} shares. Last price={last_price} figi={self.figi}"
            )

            try:
                posted_order = await client.post_order(
                    order_id=str(uuid4()),
                    figi=self.figi,
                    direction=ORDER_DIRECTION_BUY,
                    quantity=quantity_to_buy,
                    order_type=ORDER_TYPE_MARKET,
                    account_id=self.account_id,
                )
            except Exception as e:
                logger.error(f"Failed to post buy order. figi={self.figi}. {e}")
                return
            asyncio.create_task(
                self.stats_handler.handle_new_order(
                    order_id=posted_order.order_id, account_id=self.account_id
                )
            )

    async def get_last_price(self) -> float:
        """
        Get last price of the instrument.
        :return: float - last price
        """
        last_prices_response = await client.get_last_prices(figi=[self.figi])
        last_prices = last_prices_response.last_prices
        return quotation_to_float(last_prices.pop().price)

    async def validate_stop_loss(self, last_price: float) -> None:
        """
        Check if stop loss is reached. If yes, then sells all the shares.
        :param last_price: Last price of the instrument.
        """
        positions = (await client.get_portfolio(account_id=self.account_id)).positions
        position = get_position(positions, self.figi)
        if position is None:
            return
        position_price = quotation_to_float(position.average_position_price)
        if position_price < last_price:
            logger.info(f"Stop loss triggered. Last price={last_price} figi={self.figi}")
            try:
                posted_order = await client.post_order(
                    order_id=str(uuid4()),
                    figi=self.figi,
                    direction=ORDER_DIRECTION_SELL,
                    quantity=int(quotation_to_float(position.quantity)),
                    order_type=ORDER_TYPE_MARKET,
                    account_id=self.account_id,
                )
            except Exception as e:
                logger.error(f"Failed to post sell order. figi={self.figi}. {e}")
                return
            asyncio.create_task(
                self.stats_handler.handle_new_order(
                    order_id=posted_order.order_id, account_id=self.account_id
                )
            )
        return

    async def ensure_market_open(self):
        """
        Ensure that the market is open. Holds the loop until the instrument is available.
        :return: when instrument is available for trading
        """
        trading_status = await client.get_trading_status(figi=self.figi)
        while not (
            trading_status.market_order_available_flag and trading_status.api_trade_available_flag
        ):
            logger.debug(f"Waiting for the market to open. figi={self.figi}")
            await asyncio.sleep(60)
            trading_status = await client.get_trading_status(figi=self.figi)

    async def main_cycle(self):
        while True:
            try:
                await self.ensure_market_open()
                await self.update_corridor()

                orders = await client.get_orders(account_id=self.account_id)
                if get_order(orders=orders.orders, figi=self.figi):
                    logger.info(f"There are orders in progress. Waiting. figi={self.figi}")
                    continue

                last_price = await self.get_last_price()
                logger.debug(f"Last price: {last_price}, figi={self.figi}")

                await self.validate_stop_loss(last_price)

                if last_price >= self.corridor.top:
                    logger.debug(
                        f"Last price {last_price} is higher than top corridor border "
                        f"{self.corridor.top}. figi={self.figi}"
                    )
                    await self.handle_corridor_crossing_top(last_price=last_price)
                elif last_price <= self.corridor.bottom:
                    logger.debug(
                        f"Last price {last_price} is lower than bottom corridor border "
                        f"{self.corridor.bottom}. figi={self.figi}"
                    )
                    await self.handle_corridor_crossing_bottom(last_price=last_price)
            except AioRequestError as are:
                logger.error(f"Client error {are}")

            await asyncio.sleep(self.config.check_interval)

    async def start(self):
        if self.account_id is None:
            try:
                self.account_id = (await client.get_accounts()).accounts.pop().id
            except AioRequestError as are:
                logger.error(f"Error taking account id. Stopping strategy. {are}")
                return
        await self.main_cycle()
