from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from typing import List

from db.dependencies import get_db, get_current_admin_user, get_current_superadmin_user
from db.crud import get_all_categories, create_category, delete_category, get_categories_by_name
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


@router.delete("/{category_id}", status_code=status.HTTP_200_OK,
               summary="Удаление категории (только admin)")
async def delete_category_rout(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(get_current_superadmin_user),
):
    try:
        res = await delete_category(db, category_id)
        return res
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    except ValueError as e:
        linked = str(e).split()[-3]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Нельзя удалить категорию: с ней связано {linked} предложений"
        )

@router.get(
    "/search",
    response_model=List[CategoryRead],
    summary="Поиск категорий по имени (подстрока)",
    status_code=status.HTTP_200_OK
)
async def search_categories(
    title: str = Query(..., min_length=1, description="Подстрока в имени категории"),
    db: AsyncSession = Depends(get_db),
):
    cats = await get_categories_by_name(db, title)
    if not cats:
        raise HTTPException(status_code=404, detail="Категории не найдены")
    return cats