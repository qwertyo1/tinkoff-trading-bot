from typing import List, Optional

from tinkoff.invest import PortfolioPosition, OrderState


def get_position(positions: List[PortfolioPosition], figi: str) -> Optional[PortfolioPosition]:
    """
    Find position by figi

    :param positions: list of positions
    :param figi: figi of position
    :return: position or None if not found
    """
    for position in positions:
        if position.figi == figi:
            return position
    return None


def get_order(orders: List[OrderState], figi: str) -> Optional[OrderState]:
    """
    Find position by figi

    :param orders: list of orders
    :param figi: figi of order
    :return: position
    """
    for order in orders:
        if order.figi == figi:
            return order
    return None
