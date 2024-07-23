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
# TODO: move this to redis
_train, _test = load_data(refresh_train=False, refresh_test=False)


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


# app = FastAPI()

# @app.on_event("startup")
# async def startup():
#     HOST_URL = os.environ.get("REDIS_URL", LOCAL_REDIS_URL)
#     logger.info(f"Connecting to: {HOST_URL}")
#     redis = asyncio.from_url(HOST_URL)
#     FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")


@app.post("/baseline_allocate")
@cache(expire=60)
async def baseline_allocate(stocks: StockInputs) -> Allocations:
    """
    Calibrates the allocation weights using the statistical methods.
    Return is cached for 60 seconds.
    """

    tickers = stocks.get_tickers()
    missing_tickers = [t for t in tickers if t not in _test]
    if len(missing_tickers) > 0:
        raise ValueError(f"Tickers not found in the test data: {missing_tickers}")

    ticker_weights = optimize_portfolio(stocks, _train, _train.corr_matrix)
    summaries = portfolio_performance(ticker_weights, _test)

    return Allocations(ticker_weights=ticker_weights, summaries=summaries)


@app.post("/ml_allocate_cosine_similarity")
@cache(expire=60)
async def ml_allocate_cosine_similarity(stocks: StockInputs) -> Allocations:
    """
    Calibrates the allocation weights using ml-generated cosine similarity.
    Return is cached for 60 seconds.
    """

    tickers = stocks.get_tickers()
    missing_tickers = [t for t in tickers if t not in _test]
    if len(missing_tickers) > 0:
        raise ValueError(f"Tickers not found in the test data: {missing_tickers}")

    ticker_weights = optimize_portfolio(stocks, _train, _train.cosine_similarity)
    summaries = portfolio_performance(ticker_weights, _test)

    return Allocations(ticker_weights=ticker_weights, summaries=summaries)


@app.get("/refresh_data")
@cache(expire=60)
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


# @app.post("/ml_allocate_embeddings")
# @cache(expire=60)
# async def ml_allocate_embeddings(stocks: StockInputs) -> Allocations:
#     """
#     Calibrates the allocation weights using ml-generated embeddings.
#     Return is cached for 60 seconds.
#     """

#     weights = {h.ticker: 1 / len(stocks.stockList) for h in stocks.stockList}
#     summeries = [
#         PortfolioSummary(
#             name="baseline",
#             return_mean=0.1,
#             return_std=0.2,
#             sharpe_ratio=0.5,
#         ),
#         PortfolioSummary(
#             name="index",
#             return_mean=0.2,
#             return_std=0.4,
#             sharpe_ratio=0.5,
#         ),
#     ]

#     return Allocations(weights=weights, summaries=summeries)
