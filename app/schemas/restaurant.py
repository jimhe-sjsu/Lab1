from pydantic import BaseModel
from typing import Optional


class RestaurantBase(BaseModel):
    name: str
    cuisine_type: str
    address: str
    city: str
    state: str
    zip_code: str
    description: Optional[str] = None
    price_tier: Optional[str] = None


class RestaurantCreate(RestaurantBase):
    pass


class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    cuisine_type: Optional[str] = None
    description: Optional[str] = None
    price_tier: Optional[str] = None


class RestaurantResponse(RestaurantBase):
    id: int
    created_by: int
    owner_id: Optional[int]

    class Config:
        from_attributes = True