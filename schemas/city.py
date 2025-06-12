from pydantic import BaseModel


class CityBase(BaseModel):
    name: str


class CityCreate(CityBase):
    pass


class CityRead(CityBase):
    id: int

    model_config = {
        "populate_by_name": True,
        "from_attributes": True,
    }
