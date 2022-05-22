import asyncio

from tinkoff.invest import OrderExecutionReportStatus, AioRequestError

from app.client import TinkoffClient
from app.stats.sqlite_client import StatsSQLiteClient
from app.strategies.models import StrategyName
from app.utils.quotation import quotation_to_float

FINAL_ORDER_STATUSES = [
    OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_CANCELLED,
    OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_REJECTED,
    OrderExecutionReportStatus.EXECUTION_REPORT_STATUS_FILL,
]


class StatsHandler:
    def __init__(self, strategy: StrategyName, broker_client: TinkoffClient):
        self.strategy = strategy
        self.db = StatsSQLiteClient(db_name="stats.db")
        self.broker_client = broker_client

    async def handle_new_order(self, account_id: str, order_id: str) -> None:
        """
        This method is called when new order is created.
        It waits for the order to be filled, canceled, or rejected
        and logs its information to the database

        To prevent affecting the strategy execution,
        this method can be called with asyncio.create_task()

        :param account_id: id of the account the order was created for
        :param order_id: id of the order to track its status
        :return: None
        """
        try:
            order_state = await self.broker_client.get_order_state(
                account_id=account_id, order_id=order_id
            )
        except AioRequestError:
            return
        self.db.add_order(
            order_id=order_id,
            figi=order_state.figi,
            order_direction=str(order_state.direction),
            price=quotation_to_float(order_state.total_order_amount),
            quantity=order_state.lots_requested,
            status=str(order_state.execution_report_status),
        )
        while order_state.execution_report_status not in FINAL_ORDER_STATUSES:
            await asyncio.sleep(10)
            order_state = await self.broker_client.get_order_state(
                account_id=account_id, order_id=order_id
            )
        self.db.update_order_status(
            order_id=order_id, status=str(order_state.execution_report_status)
        )
