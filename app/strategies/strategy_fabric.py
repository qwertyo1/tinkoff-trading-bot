from typing import Dict

from app.strategies.interval.IntervalStrategy import IntervalStrategy
from app.strategies.base import BaseStrategy
from app.strategies.errors import UnsupportedStrategyError
from app.strategies.models import StrategyName

strategies: Dict[StrategyName, BaseStrategy.__class__] = {
    StrategyName.INTERVAL: IntervalStrategy,
}


def resolve_strategy(strategy_name: StrategyName, figi: str, *args, **kwargs) -> BaseStrategy:
    if strategy_name not in strategies:
        raise UnsupportedStrategyError(strategy_name)
    return strategies[strategy_name](figi=figi, *args, **kwargs)
