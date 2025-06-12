from pydantic import BaseModel, Field, HttpUrl


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    imageUrl: HttpUrl = Field(alias="image_url")


class CategoryCreate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    id: int

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
