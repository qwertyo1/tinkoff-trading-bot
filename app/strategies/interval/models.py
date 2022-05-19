from pydantic import BaseModel, Field


class IntervalStrategyConfig(BaseModel):
    interval_size: float = Field(0.8, ge=0.0, le=1.0)
    days_back_to_consider: int = Field(30, g=0)
    corridor_update_interval: int = Field(600, g=0)
    check_interval: int = Field(60, g=0)
    stop_loss_percentage: float = Field(0.1, ge=0.0, le=1.0)
    quantity_limit: int = Field(0, g=0)


class Corridor(BaseModel):
    top: float
    bottom: float
