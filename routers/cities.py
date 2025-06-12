from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from typing import List

from db.dependencies import get_db, get_current_active_user, get_current_admin_user
from db.crud import get_all_cities, create_city
from schemas.city import CityCreate, CityRead

router = APIRouter(prefix="/api/cities", tags=["cities"])


@router.get("/", response_model=List[CityRead], summary="Получение списка всех городов")
async def read_cities(db: AsyncSession = Depends(get_db)):
    cities = await get_all_cities(db)
    return cities


@router.post("/", response_model=CityRead, status_code=status.HTTP_201_CREATED, summary="Добавление нового города")
async def add_city(
    city_in: CityCreate,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(get_current_admin_user)
):
    """
    Только администратор может добавлять города.
    """
    try:
        city = await create_city(db, city_in.name)
        return city
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Город с таким именем уже существует")
