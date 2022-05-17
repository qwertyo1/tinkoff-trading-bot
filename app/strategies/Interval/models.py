from pydantic import BaseModel, Field


class IntervalStrategyConfig(BaseModel):
    interval_size: float = Field(0.8, ge=0.0, le=1.0)
    days_back_to_consider: int = Field(30, g=0)
