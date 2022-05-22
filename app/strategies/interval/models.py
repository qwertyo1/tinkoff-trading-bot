from pydantic import BaseModel, Field


class IntervalStrategyConfig(BaseModel):
    """
    Interval Strategy Configuration

    interval_size: The percent of the prices to include into interval
    days_back_to_consider: The number of days back to consider in interval calculation
    check_interval: The interval in seconds to check for a new prices and for interval recalculation
    stop_loss_percent: The percent from the price to trigger a stop loss
    quantity_limit: The maximum quantity of the instrument to have in the portfolio
    """

    interval_size: float = Field(0.8, ge=0.0, le=1.0)
    days_back_to_consider: int = Field(30, g=0)
    check_interval: int = Field(60, g=0)
    stop_loss_percentage: float = Field(0.1, ge=0.0, le=1.0)
    quantity_limit: int = Field(0, ge=0)


class Corridor(BaseModel):
    top: float
    bottom: float
