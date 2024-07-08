import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import joblib
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from redis import asyncio

from src.server.data_model import Allocations, House, Price, StockInputs

LOCAL_REDIS_URL = "redis://localhost:6379/"

logger = logging.getLogger(__name__)
# TODO: replace this with the S3 download of the stock embeddings, and generate the cosine similarity matrix
# TODO: put embeddings into the REDIS for faster access
# model_path = Path(__file__).parent.parent / "model_pipeline.pkl"
# model = joblib.load(model_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """This specifies the startup and shutdown events for the FastAPI app.

    Args:
        app (FastAPI): _description_
    """
    HOST_URL = os.environ.get("REDIS_URL", LOCAL_REDIS_URL)
    logger.debug(HOST_URL)
    redis = asyncio.from_url(HOST_URL, encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

    yield


app = FastAPI(lifespan=lifespan)


# app = FastAPI()

# @app.on_event("startup")
# async def startup():
#     HOST_URL = os.environ.get("REDIS_URL", LOCAL_REDIS_URL)
#     logger.info(f"Connecting to: {HOST_URL}")
#     redis = asyncio.from_url(HOST_URL)
#     FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")


@app.get("/hello")
@cache(expire=60)
async def hello(name: str):
    """
    This endpoint returns a message with the name passed as a query parameter.
    """
    message = f"hello {name}"
    return {"message": message}


@app.get("/health")
async def health():
    """
    This endpoint returns the current date/time in ISO8601 format.
    """
    return {"time": datetime.now().isoformat()}


# TODO: update this below per notebook
# /baseline_allocate
# /ml_allocate_embeddings
# /ml_allocate_cosine_similarity
@app.post("/baseline_allocate")
@cache(expire=60)
async def baseline_allocate(stocks: StockInputs) -> Allocations:
    """
    This endpoint calibrates the allocation weights using the statistical methods.
    This endpoint's return is cached for 60 seconds.
    """

    # perform predictions
    predictions = [123]  # model.predict(houses.to_numpy())

    # construct the output
    return Allocations(prices=predictions)
