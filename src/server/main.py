import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from redis import asyncio

from src.ray.optimizer.portfolios import optimize_portfolio, portfolio_performance
from src.server.data_factory import load_data
from src.server.data_model import Allocations, StockInputs

LOCAL_REDIS_URL = "redis://localhost:6379/"

logger = logging.getLogger(__name__)
REFRESH_TRAIN = os.environ.get("REFRESH_TRAIN") == "True"
_td, _test = load_data(refresh_train=REFRESH_TRAIN, refresh_test=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    This specifies the startup and shutdown events for the FastAPI app.
    """
    HOST_URL = os.environ.get("REDIS_URL", LOCAL_REDIS_URL)
    logger.debug(HOST_URL)
    redis = asyncio.from_url(HOST_URL, encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

    yield


app = FastAPI(
    lifespan=lifespan,
    swagger_ui_parameters={
        "syntaxHighlight.theme": "arta",
        "defaultModelExpandDepth": 1,
        "defaultModelRendering": "model",
    },
)


@app.post("/baseline_allocate")
@cache(expire=1200)
async def baseline_allocate(stocks: StockInputs) -> Allocations:
    """
    Calibrates the allocation weights using the statistical methods.
    Return is cached for 60 seconds.
    """

    coeff_name = "baseline"
    return allocate(stocks, coeff_name)


@app.post("/ml_allocate_cosine_similarity")
@cache(expire=60)
async def ml_allocate_cosine_similarity(stocks: StockInputs) -> Allocations:
    """
    Calibrates the allocation weights using ml-generated cosine similarity.
    Return is cached for 60 seconds.
    """

    coeff_name = "ml_baseline"
    return allocate(stocks, coeff_name)


@app.post("/ml_allocate_dynamic_avg")
@cache(expire=1200)
async def ml_allocate_dynamic_avg(stocks: StockInputs) -> Allocations:
    """
    Calibrates the allocation weights using ml-generated cosine similarity.
    Return is cached for 60 seconds.
    """

    coeff_name = "ml_ave_output"
    return allocate(stocks, coeff_name)


@app.post("/ml_allocate_dynamic_last")
@cache(expire=1200)
async def ml_allocate_dynamic_last(stocks: StockInputs) -> Allocations:
    """
    Calibrates the allocation weights using ml-generated cosine similarity.
    Return is cached for 60 seconds.
    """

    coeff_name = "ml_last_output"
    return allocate(stocks, coeff_name)


@app.get("/refresh_data")
async def refresh_data():
    """
    refresh the test data from yahoo finance.
    """
    global _test
    _, _test = load_data(refresh_train=False, refresh_test=True)

    return {f"message: Data refreshed. Newest test data: {_test.index.max()}"}


@app.get("/health")
async def health():
    """
    This endpoint returns the current date/time in ISO8601 format.
    """
    return {"time": datetime.now().isoformat()}


def allocate(stocks: StockInputs, coeff_name: str) -> Allocations:
    """
    Calibrates the allocation weights using the statistical methods.
    """

    tickers = stocks.get_tickers()
    missing_tickers = [t for t in tickers if t not in _test]
    if len(missing_tickers) > 0:
        raise ValueError(f"Tickers not found in the test data: {missing_tickers}")

    if coeff_name not in _td.coeff_dict:
        raise ValueError(f"Invalid coefficient name: {coeff_name}")

    ticker_weights = optimize_portfolio(stocks, _td, _td.coeff_dict[coeff_name])
    summaries = portfolio_performance(ticker_weights, _test)

    return Allocations(ticker_weights=ticker_weights, summaries=summaries)
