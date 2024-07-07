import asyncio
from typing import Any, Generator

import pytest
from fastapi.testclient import TestClient
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

from src.server.main import app

bulk_calibrate_endpoint = "/bulk_calibrate"


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
    "input, expected_code",
    [
        (
            {
                "houses": [
                    {
                        "med_income": 8.3,
                        "house_age": 41.0,
                        "ave_room_num": 7.1,
                        "ave_bedrm_num": 1.02,
                        "population": 322.0,
                        "ave_occup": 2.56,
                        "latitude": 37.88,
                        "longitude": -122.23,
                    },
                    {
                        "med_income": 8.3,
                        "house_age": 41.0,
                        "ave_room_num": 7.1,
                        "ave_bedrm_num": 1.02,
                        "population": 322.0,
                        "ave_occup": 2.56,
                        "latitude": 37.88,
                        "longitude": -122.23,
                    },
                ]
            },
            200,
        ),
        (
            {
                # jazz up the input a bit
                "houses": [
                    {
                        "med_income": 8.3,
                        "house_age": "41.0",  # string format is also accepted
                        "ave_room_num": 7,  # int format is also accepted
                        "ave_bedrm_num": 1.02,
                        "population": "0.322e3",  # scientific notation is also accepted
                        "ave_occup": 2.6,
                        "latitude": 37.88,
                        "longitude": -122.23,
                    },
                    {
                        "med_income": 8.3,
                        "house_age": "41.0",
                        "ave_room_num": 7,
                        "ave_bedrm_num": 1.02,
                        "population": "0.322e3",
                        "ave_occup": 2.6,
                        "latitude": 37.88,
                        "longitude": -122.23,
                    },
                ]
            },
            200,
        ),
    ],
)
def test_bulk_houses_model(input, expected_code):
    with TestClient(app) as client:
        # test the first call
        response = client.post(bulk_calibrate_endpoint, json=input)
        assert response.status_code == expected_code
        response_json = response.json()

        assert "hash_key" in response_json

        assert "prices" in response_json
        prices_list = response_json["prices"]
        assert len(prices_list) == 2
        assert all(p > 0 for p in prices_list)

        # test cache a little bit -> should return the same hash_key
        previous_hash_key = response_json["hash_key"]

        new_response = client.post(bulk_calibrate_endpoint, json=input)
        assert new_response.status_code == expected_code
        new_response_json = new_response.json()

        assert "hash_key" in new_response_json
        assert previous_hash_key == new_response_json["hash_key"]


def test_bulk_calibrate_with_extra_input():
    houses_data = {
        "houses": [
            {
                "med_income": 8.3,
                "house_age": 41.0,
                "ave_room_num": 7,
                "ave_bedrm_num": 1.02,
                "population": 322.0,
                "ave_occup": 2.6,
                "latitude": 37.88,
                "longitude": -122.23,
                "extra_field": 123,
            },
        ]
    }

    with TestClient(app) as client:
        response = client.post(bulk_calibrate_endpoint, json=houses_data)
        assert response.status_code == 422
        assert "detail" in response.json()
        assert "Extra inputs are not permitted" in response.json()["detail"][0]["msg"]


def test_bulk_calibrate_with_missing_input():
    houses_data = {
        "houses": [
            {
                "med_income": 8.3,
                "house_age": 41.0,
                "ave_room_num": 7,
                "ave_bedrm_num": 1.02,
                "population": 322.0,
                "latitude": 37.88,
                "longitude": -122.23,
            },
        ]
    }

    with TestClient(app) as client:
        response = client.post(bulk_calibrate_endpoint, json=houses_data)
        assert response.status_code == 422
        assert "detail" in response.json()
        assert "Field required" in response.json()["detail"][0]["msg"]


def test_bulk_calibrate_with_invalid_negative_input():
    houses_data = {
        "houses": [
            {
                "med_income": 8.3,
                "house_age": 41.0,
                "ave_room_num": 7,
                "ave_bedrm_num": 1.02,
                "population": -322.0,
                "ave_occup": 2.6,
                "latitude": 37.88,
                "longitude": -122.23,
            },
        ]
    }

    with TestClient(app) as client:
        response = client.post(bulk_calibrate_endpoint, json=houses_data)
        assert response.status_code == 422
        assert "detail" in response.json()
        assert "greater than or equal to 0" in response.json()["detail"][0]["msg"]


def test_bulk_calibrate_with_bad_input():
    houses_data = {
        "houses": [
            {
                "med_income": 8.3,
                "house_age": 41.0,
                "ave_room_num": 7,
                "ave_bedrm_num": 1.02,
                "population": "I'm bad",
                "ave_occup": 2.6,
                "latitude": 37.88,
                "longitude": -122.23,
            },
        ]
    }

    with TestClient(app) as client:
        response = client.post(bulk_calibrate_endpoint, json=houses_data)
        assert response.status_code == 422
        assert "detail" in response.json()
        assert "Input should be a valid number" in response.json()["detail"][0]["msg"]
