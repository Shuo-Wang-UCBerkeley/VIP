from uuid import UUID, uuid4

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator

"""
Input data models
"""


class House(BaseModel):
    """
    input data model for the singular predict endpoint.
    """

    med_income: float = Field(ge=0, description="Median Income must be >=0")
    house_age: float = Field(ge=0, description="House Age must be >=0")
    ave_room_num: float = Field(ge=0, description="Average Rooms must be >=0")
    ave_bedrm_num: float = Field(ge=0, description="Average Bedroom must be >=0")
    population: float = Field(ge=0, description="Population must be >=0")
    ave_occup: float = Field(ge=0, description="Average Occupancy must be >=0")
    latitude: float
    longitude: float

    def to_numpy(self):
        """
        convert the input data into a numpy 1D array

        Returns:
            ndarray: 1D numpy array
        """
        return np.fromiter(self.model_dump().values(), float)

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "med_income": 8.3,
                    "house_age": 41.0,
                    "ave_room_num": 7.1,
                    "ave_bedrm_num": 1.02,
                    "population": 322.0,
                    "ave_occup": 2.56,
                    "latitude": 37.88,
                    "longitude": -122.23,
                }
            ]
        },
    )

    @field_validator("latitude")
    def validate_latitude(cls, latitude_input):
        if latitude_input < -90 or latitude_input > 90:
            raise ValueError("Latitude must be between -90 and 90 degrees!")
        return latitude_input

    @field_validator("longitude")
    def validate_longtitude(cls, longitude_input):
        if longitude_input < -180 or longitude_input > 180:
            raise ValueError("Longitude must be between -180 and 180 degrees!")
        return longitude_input


class BulkHouses(BaseModel):
    """
    input data model for the bulk predict endpoint.
    """

    houses: list[House]

    def to_numpy(self):
        """
        convert the input data into a numpy 2D array

        Returns:
            ndarray: 2D numpy array
        """
        return np.vstack([h.to_numpy() for h in self.houses])

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
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
                }
            ]
        },
    )


"""
Output data models
"""


class Price(BaseModel):
    """
    output prediction price for the singular predict endpoint.
    """

    price: float


class BulkPrices(BaseModel):
    """
    output prediction price for the bulk predict endpoint.
    """

    hash_key: UUID = Field(default_factory=uuid4)
    prices: list[float]
