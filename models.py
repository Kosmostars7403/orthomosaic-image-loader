from datetime import datetime

from bson import ObjectId
from pydantic import BaseModel, Field


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class FlightReport(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    path_to_images: str = Field(...)
    type: str = Field(...)
    flight_date: datetime = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                'path_to_folder': 'uploads',
                'type': 'TEST',
                'flight_date': None
            }
        }
