from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from typing import List

from db.dependencies import get_db, get_current_admin_user
from db.crud import get_all_categories, create_category
from schemas.category import CategoryCreate, CategoryRead

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("/", response_model=List[CategoryRead], summary="Получение списка всех категорий")
async def read_categories(db: AsyncSession = Depends(get_db)):
    categories = await get_all_categories(db)
    return categories


@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED, summary="Добавление новой категории")
async def add_category(
    category_in: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(get_current_admin_user)
):
    """
    Только администратору разрешено добавлять категории.
    """
    try:
        category = await create_category(db, category_in.name, category_in.imageUrl)
        return category
    except Exception as e:
        print(e)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Категория с таким именем уже существует")
