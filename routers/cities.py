from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from typing import List

from db.dependencies import get_db, get_current_active_user, get_current_admin_user, get_current_superadmin_user
from db.crud import get_all_cities, create_city, delete_city, get_cities_by_name
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

@router.delete("/{city_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Удаление города")
async def delete_city_rout(
    city_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(get_current_superadmin_user),
):
    try:
        count = await delete_city(db, city_id)
        return count
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Город не найден")
    except ValueError as e:
        # есть связанные предложения
        # e.args[0] содержит, например, "City 5 has 3 linked offers"
        linked = str(e).split()[-3]  # число
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Нельзя удалить город: с ним связано {linked} предложений"
        )

@router.get(
    "/search",
    response_model=List[CityRead],
    summary="Поиск городов по имени (подстрока)",
    status_code=status.HTTP_200_OK
)
async def search_cities(
    title: str = Query(..., min_length=1, description="Подстрока в имени города"),
    db: AsyncSession = Depends(get_db),
):
    cities = await get_cities_by_name(db, title)
    if not cities:
        raise HTTPException(status_code=404, detail="Города не найдены")
    return cities