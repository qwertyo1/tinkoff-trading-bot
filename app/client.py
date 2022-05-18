# TODO: handle errors:
#   - AioRpcError with different codes (StatusCode)

from datetime import datetime
from typing import Optional, List

from tinkoff.invest import AsyncClient, CandleInterval, Quotation, OrderDirection, OrderType
from tinkoff.invest.async_services import AsyncServices

from app.settings import settings


class TinkoffClient:
    def __init__(self, token: str, sandbox: bool = False):
        self.token = token
        self.sandbox = sandbox
        self.client: Optional[AsyncServices] = None

    async def ainit(self):
        self.client = await AsyncClient(self.token).__aenter__()

    async def get_orders(self, account_id: str):
        if self.sandbox:
            return await self.client.sandbox.get_sandbox_orders(account_id=account_id)
        return await self.client.orders.get_orders(account_id=account_id)

    async def get_portfolio(self, account_id: str):
        if self.sandbox:
            return await self.client.sandbox.get_sandbox_portfolio(account_id=account_id)
        return await self.client.operations.get_portfolio(account_id=account_id)

    async def get_accounts(self):
        if self.sandbox:
            return await self.client.sandbox.get_sandbox_accounts()
        return await self.client.users.get_accounts()

    async def get_all_candles(
        self,
        from_: datetime,
        to: Optional[datetime] = None,
        interval: CandleInterval = CandleInterval(0),
        figi: str = "",
    ):
        async for candle in self.client.get_all_candles(
            from_=from_, to=to, interval=interval, figi=figi
        ):
            yield candle

    async def get_last_prices(self, figi: Optional[List[str]] = None):
        last_prices = await self.client.market_data.get_last_prices(figi=figi)
        return last_prices

    async def post_order(
        self,
        figi: str = "",
        quantity: int = 0,
        price: Optional[Quotation] = None,
        direction: OrderDirection = OrderDirection(0),
        account_id: str = "",
        order_type: OrderType = OrderType(0),
        order_id: str = "",
    ):
        if self.sandbox:
            return await self.client.sandbox.post_sandbox_order(
                figi=figi,
                quantity=quantity,
                price=price,
                direction=direction,
                account_id=account_id,
                order_type=order_type,
                order_id=order_id,
            )
        return await self.client.orders.post_order(
            figi=figi,
            quantity=quantity,
            price=price,
            direction=direction,
            account_id=account_id,
            order_type=order_type,
            order_id=order_id,
        )


client = TinkoffClient(token=settings.token, sandbox=settings.sandbox)
