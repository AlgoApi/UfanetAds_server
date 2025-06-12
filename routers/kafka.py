from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from typing import List

from db.dependencies import get_db, get_current_active_user, get_current_admin_user
from db.crud import get_all_cities, create_city
from schemas.city import CityCreate, CityRead

router = APIRouter(prefix="/api/kafka", tags=["kafka"])

