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

    # validate the risk tolerance
    @field_validator("risk_tolerance")
    def validate_risk_tolerance(cls, risk_tolerance_input):
        if risk_tolerance_input not in ["low", "moderate", "high"]:
            raise ValueError("Risk tolerance must be one of 'low', 'moderate', 'high'!")
        return risk_tolerance_input

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
                        {"ticker": "ORCL"},
                        {"ticker": "MSFT"},
                        {"ticker": "NVDA"},
                        {"ticker": "JPM"},
                        {"ticker": "CVX"},
                        {"ticker": "GILD"},
                        {"ticker": "TSLA"},
                        {"ticker": "AMZN"},
                    ],
                    "risk_tolerance": "medium",
                },
                {
                    "stockList": [
                        {
                            # range of weights
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
                        {
                            # only lower bound
                            "ticker": "NVDA",
                            "weight_lower_bound": 0.25,
                        },
                    ],
                    "risk_tolerance": "moderate",
                },
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
    mean_return: float = Field(description="Mean return")
    total_return: float = Field(description="Total return for the test period")
    volatility: float = Field(description="Standard deviation of return")
    sharpe_ratio: float = Field(description="Sharpe ratio")

    # constructor with rounding
    def __init__(self, **data):
        super().__init__(**data)
        self.mean_return = round(self.mean_return, 2)
        self.total_return = round(self.total_return, 2)
        self.volatility = round(self.volatility, 2)
        self.sharpe_ratio = round(self.sharpe_ratio, 2)


class Allocations(BaseModel):
    """
    output allocation weights and stats.
    """

    ticker_weights: dict[str, float] = Field(description="Stock ticker to suggested weights")
    summaries: list[PortfolioSummary] = Field(
        description="Portfolio metadata, for both the allocated portfolio and S&P 500 index."
    )
    # hash_key: UUID = Field(default_factory=uuid4, description="Unique hash key per return, used to validate cache")

    # constructor with rounding
    def __init__(self, **data):
        super().__init__(**data)
        self.ticker_weights = {k: round(v, 4) for k, v in self.ticker_weights.items()}

    # validation on weights sum to 1
    @field_validator("ticker_weights")
    def validate_weights(cls, weights_input):
        if not np.isclose(sum(weights_input.values()), 1):
            raise ValueError("Weights must sum to 1!")
        return weights_input
