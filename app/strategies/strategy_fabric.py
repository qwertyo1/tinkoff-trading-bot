from typing import Dict

from app.strategies.interval.IntervalStrategy import IntervalStrategy
from app.strategies.base import BaseStrategy
from app.strategies.errors import UnsupportedStrategyError
from app.strategies.models import StrategyName

strategies: Dict[StrategyName, BaseStrategy.__class__] = {
    StrategyName.INTERVAL: IntervalStrategy,
}


def resolve_strategy(strategy_name: StrategyName, figi: str, *args, **kwargs) -> BaseStrategy:
    """
    Creates strategy instance by strategy name. Passes all arguments to strategy constructor.

    :param strategy_name: the name of strategy. See :class:`app.strategies.models.StrategyName`
    :param figi: the figi of the instrument strategy applied to
    :return: strategy instance. See :class:`app.strategies.base.BaseStrategy`
    :raises: :class:`app.strategies.errors.UnsupportedStrategyError` if the name is not supported
    """
    if strategy_name not in strategies:
        raise UnsupportedStrategyError(strategy_name)
    return strategies[strategy_name](figi=figi, *args, **kwargs)
