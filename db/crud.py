from typing import Any, Coroutine, Sequence

from pydantic import HttpUrl
from sqlalchemy.future import select
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from db.models import User, RoleEnum, City, Category, Offer, Stat, offer_city, offer_category
from core.security import get_password_hash

# --- Пользователи ---

async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalars().first()

async def create_user(db: AsyncSession, username: str, password: str, role: RoleEnum = RoleEnum.user) -> User:
    hashed = get_password_hash(password)
    new_user = User(username=username, hashed_password=hashed, role=role)
    db.add(new_user)
    try:
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except IntegrityError:
        await db.rollback()
        raise

# --- Города ---

async def get_all_cities(db: AsyncSession) -> Sequence[City]:
    result = await db.execute(select(City))
    return result.scalars().all()

async def create_city(db: AsyncSession, name: str) -> City:
    city = City(name=name)
    db.add(city)
    try:
        await db.commit()
        await db.refresh(city)
        return city
    except IntegrityError:
        await db.rollback()
        raise

# --- Категории ---

async def get_all_categories(db: AsyncSession) -> Sequence[Category]:
    result = await db.execute(select(Category))
    return result.scalars().all()

async def create_category(db: AsyncSession, name: str, image_url: str|HttpUrl) -> Category:
    category = Category(name=name, imageUrl=str(image_url))
    db.add(category)
    try:
        await db.commit()
        await db.refresh(category)
        return category
    except IntegrityError:
        await db.rollback()
        raise

# --- Предложения ---

async def get_offers_by_city_and_category(
    db: AsyncSession, city_id: int, category_id: int | None = None, limit: int = 5, offset: int = 0
) -> Sequence[Offer]:
    query = select(Offer).join(offer_city).where(offer_city.c.city_id == city_id)
    if category_id is not None:
        query = query.join(offer_category).where(offer_category.c.category_id == category_id)
    query = query.options(
        selectinload(Offer.cities),
        selectinload(Offer.categories)
    )
    query = query.order_by(Offer.created_at).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()

async def create_offer(db: AsyncSession, title: str, description: str|None,
                       cities_ids: list[int], categories_ids: list[int],
                       background_image_url: str | HttpUrl,
                       company_logo_url: str | HttpUrl,
                       company_name: str) -> Offer:
    if len(categories_ids) > 2:
        raise ValueError("нельзя больше двух категорий")

    offer = Offer(
        title=title,
        description=description,
        background_image_url=str(background_image_url),
        company_logo_url=str(company_logo_url),
        company_name=company_name
    )

    db.add(offer)
    await db.flush()

    # Добавляем города
    for cid in cities_ids:
        await db.execute(
            insert(offer_city).values(offer_id=offer.id, city_id=cid)
        )

    # Добавляем категории (не более 2)
    for catid in categories_ids:
        await db.execute(
            insert(offer_category).values(offer_id=offer.id, category_id=catid)
        )

    try:
        await db.commit()
        await db.refresh(offer)
        return offer
    except IntegrityError:
        await db.rollback()
        raise

# --- Статистика ---

async def log_stat(db: AsyncSession, user_id: int, offer_id: int) -> Stat:
    stat = Stat(user_id=user_id, offer_id=offer_id)
    db.add(stat)
    await db.commit()
    await db.refresh(stat)
    return stat
