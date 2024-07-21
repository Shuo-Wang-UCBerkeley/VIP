from uuid import UUID, uuid4

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator

"""
Input data models
"""


class StockPara(BaseModel):
    """
    input data model for the singular input.
    """

    ticker: str = Field(description="Stock Ticker")
    weight_lower_bound: float = Field(ge=0, description="Weight lower bound, must be >=0 (no shorting)", default=0.0)
    weight_upper_bound: float = Field(le=1, description="Weight upper bound, must be <=1 (no leverage)", default=1.0)

    def to_numpy(self):
        """
        convert the input data into a numpy 1D array

        Returns:
            ndarray: 1D numpy array
        """
        return np.fromiter(self.model_dump().values(), float)

    def get_bounds(self):
        """
        get the weight bounds for the stock

        Returns:
            tuple: weight bounds
        """
        if self.weight_lower_bound > self.weight_upper_bound:
            raise ValueError(f"For ticker {self.ticker}, weight lower bound > weight upper bound!")

        return (self.weight_lower_bound, self.weight_upper_bound)

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "ticker": "AAPL",
                    "weight_lower_bound": 0.05,
                    "weight_upper_bound": 0.15,
                }
            ]
        },
    )


class StockInputs(BaseModel):
    """
    input data model for the list of inputs.
    """

    stockList: list[StockPara]
    risk_tolerance: str = Field(
        description="Risk tolerance level, options: 'low', 'moderate' and 'high'", default="low"
    )
    """
    low risk tolerance will use minimum variance optimization, high risk tolerance will use max sharpe ratio optimization
    """

    def to_numpy(self):
        """
        convert the input data into a numpy 2D array

        Returns:
            ndarray: 2D numpy array
        """
        return np.vstack([s.to_numpy() for s in self.stockList])

    def get_tickers(self):
        """
        get the tickers for the stocks

        Returns:
            list: tickers
        """
        return [h.ticker for h in self.stockList]

    def get_bounds(self):
        """
        get the weight bounds for the stocks

        Returns:
            tuple: weight bounds
        """
        return [h.get_bounds() for h in self.stockList]

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "stockList": [
                        {
                            "ticker": "AAPL",
                            "weight_lower_bound": 0.05,
                            "weight_upper_bound": 0.15,
                        },
                        {
                            # fixed weight
                            "ticker": "AMZN",
                            "weight_lower_bound": 0.35,
                            "weight_upper_bound": 0.35,
                        },
                        {
                            # unconstrained weight
                            "ticker": "GOOGL",
                        },
                    ],
                    "risk_tolerance": "low",
                }
            ]
        },
    )


"""
Output data models
"""


class PortfolioSummary(BaseModel):
    """
    portfolio meta data based on testing period performance.
    """

    name: str = Field(description="Portfolio name")
    return_mean: float = Field(description="Mean return")
    return_std: float = Field(description="Standard deviation of return")
    sharpe_ratio: float = Field(description="Sharpe ratio")
    total_return: float = Field(description="Total return for the test period")


class Allocations(BaseModel):
    """
    output allocation weights and stats.
    """

    ticker_weights: dict[str, float] = Field(description="Stock ticker to suggested weights")
    summaries: list[PortfolioSummary] = Field(
        description="Portfolio metadata, for both the allocated portfolio and S&P 500 index."
    )
    hash_key: UUID = Field(default_factory=uuid4, description="Unique hash key per return, used to validate cache")

    # validation on weights sum to 1
    @field_validator("weights")
    def validate_weights(cls, weights_input):
        if not np.isclose(sum(weights_input.values()), 1):
            raise ValueError("Weights must sum to 1!")
        return weights_input
