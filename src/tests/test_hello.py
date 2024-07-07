import asyncio
from typing import Any, Generator

import pytest
from fastapi.testclient import TestClient
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

from src.server.main import app

client = TestClient(app)

hello_endpoint = "/hello"
missing_field_msg = "Field required"


@pytest.fixture(autouse=True)
def _init_cache() -> Generator[Any, Any, None]:
    """
    Initialize the cache before each test and clear it after each test.
    Needed to mock the redis cache for testing.
    """
    FastAPICache.init(InMemoryBackend())
    yield
    asyncio.run(FastAPICache.clear())


@pytest.mark.parametrize(
    "input, expected_code, expected_response",
    [
        ("?name=James", 200, {"message": "hello James"}),
        ("?name=2", 200, {"message": "hello 2"}),
    ],
)
def test_hello_with_correct_input(input, expected_code, expected_response):
    response = client.get(f"{hello_endpoint}{input}")

    assert response.status_code == expected_code

    assert response.json() == expected_response


def test_hello_with_wrong_input():
    response = client.get(f"{hello_endpoint}?na=James")

    assert response.status_code == 422

    assert response.json().get("detail")[0].get("msg") == missing_field_msg


def test_hello_without_name_parameter():
    response = client.get(f"{hello_endpoint}")

    assert response.status_code == 422

    assert response.json().get("detail")[0].get("msg") == missing_field_msg


def test_root():
    response = client.get("/")

    assert response.status_code == 404

    assert response.json() == {"detail": "Not Found"}


# test health endpoint
def test_health():
    response = client.get("/health")

    assert response.status_code == 200

    assert response.json().get("time") is not None
    assert response.json().get("time") != ""
    assert isinstance(response.json().get("time"), str)
    assert response.json().get("time").count("-") == 2
