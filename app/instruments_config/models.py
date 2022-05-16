from typing import Any, Dict, List

from pydantic import BaseModel

from app.strategies.models import StrategyName


class StrategyConfig(BaseModel):
    name: StrategyName
    parameters: Dict[str, Any]


class InstrumentConfig(BaseModel):
    figi: str
    strategy: StrategyConfig


class InstrumentsConfig(BaseModel):
    instruments: List[InstrumentConfig]
