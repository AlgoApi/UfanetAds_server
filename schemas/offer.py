from datetime import datetime

from pydantic import BaseModel, HttpUrl, Field
from typing import Optional

from schemas.category import CategoryRead
from schemas.city import CityRead


class OfferBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    backgroundImageUrl: HttpUrl = Field(alias="background_image_url")
    companyLogoUrl: HttpUrl = Field(alias="company_logo_url")
    companyName: str = Field(..., min_length=1, max_length=100, alias="company_name")

class OfferCreate(OfferBase):
    cities_ids: list[int]
    categories_ids: list[int]


class OfferRead(OfferBase):
    id: int
    created_at: datetime

    #category: Optional["CategoryRead"] = None

    model_config = {
        "populate_by_name": True,
        "from_attributes": True,
    }

OfferRead.model_rebuild()