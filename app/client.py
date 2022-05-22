from datetime import datetime
from typing import Optional, List

from tinkoff.invest import (
    AsyncClient,
    CandleInterval,
    Quotation,
    OrderDirection,
    OrderType,
    PostOrderResponse,
    GetLastPricesResponse,
    OrderState,
    GetTradingStatusResponse,
)
from tinkoff.invest.async_services import AsyncServices

from app.settings import settings


class TinkoffClient:
    """
    Wrapper for tinkoff.invest.AsyncClient.
    Takes responsibility for choosing correct function to call basing on sandbox mode flag.
    """

    def __init__(self, token: str, sandbox: bool = False):
        self.token = token
        self.sandbox = sandbox
        self.client: Optional[AsyncServices] = None

    async def ainit(self):
        self.client = await AsyncClient(token=self.token, app_name="qwertyo1").__aenter__()

    async def get_orders(self, **kwargs):
        if self.sandbox:
            return await self.client.sandbox.get_sandbox_orders(**kwargs)
        return await self.client.orders.get_orders(**kwargs)

    async def get_portfolio(self, **kwargs):
        if self.sandbox:
            return await self.client.sandbox.get_sandbox_portfolio(**kwargs)
        return await self.client.operations.get_portfolio(**kwargs)

    async def get_accounts(self):
        if self.sandbox:
            return await self.client.sandbox.get_sandbox_accounts()
        return await self.client.users.get_accounts()

    async def get_all_candles(self, **kwargs):
        async for candle in self.client.get_all_candles(**kwargs):
            yield candle

    async def get_last_prices(self, **kwargs) -> GetLastPricesResponse:
        return await self.client.market_data.get_last_prices(**kwargs)

    async def post_order(self, **kwargs) -> PostOrderResponse:
        if self.sandbox:
            return await self.client.sandbox.post_sandbox_order(**kwargs)
        return await self.client.orders.post_order(**kwargs)

    async def get_order_state(self, **kwargs) -> OrderState:
        if self.sandbox:
            return await self.client.sandbox.get_sandbox_order_state(**kwargs)
        return await self.client.orders.get_order_state(**kwargs)

    async def get_trading_status(self, **kwargs) -> GetTradingStatusResponse:
        return await self.client.market_data.get_trading_status(**kwargs)


client = TinkoffClient(token=settings.token, sandbox=settings.sandbox)
