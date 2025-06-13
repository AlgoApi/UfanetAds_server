from typing import Any, Coroutine, Sequence, List
from sqlalchemy.dialects.postgresql import insert as pg_insert
from pydantic import HttpUrl
from sqlalchemy.future import select
from sqlalchemy import insert, delete, func, Row, RowMapping
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from db.models import User, RoleEnum, City, Category, Offer, Stat, offer_city, offer_category
from core.security import get_password_hash

# --- etc ---
def count_affected(result):
    count = result.rowcount or 0
    if count == 0:
        raise NoResultFound()
    return count

async def count_offers_for_city(db: AsyncSession, city_id: int) -> int:
    return await db.scalar(
        select(func.count()).select_from(offer_city).where(
            offer_city.c.city_id == city_id
        )
    ) or 0

async def count_offers_for_category(db: AsyncSession, category_id: int) -> int:
    return await db.scalar(
        select(func.count()).select_from(offer_category).where(
            offer_category.c.category_id == category_id
        )
    ) or 0


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

async def get_cities_by_name(
    db: AsyncSession,
    name_substr: str
) -> Sequence[City]:
    stmt = (
        select(City)
        .where(City.name.ilike(f"%{name_substr}%"))
        .order_by(City.name)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def delete_city(db: AsyncSession, city_id: int) -> int:
    linked = await count_offers_for_city(db, city_id)
    if linked > 0:
        # не удаляем, возвращаем признак ошибки
        raise ValueError(f"Город {city_id} связан {linked} раз к предложению")
    result = await db.execute(delete(City).where(City.id == city_id))
    count = count_affected(result)
    await db.commit()
    return count

async def add_city_to_offer(db: AsyncSession, offer_id: int, city_id: int):
    offer = await db.get(Offer, offer_id)
    if not offer:
        raise NoResultFound(f"Offer {offer_id} not found")

    city = await db.get(City, city_id)
    if not city:
        raise NoResultFound(f"City {city_id} not found")

    stmt = pg_insert(offer_city).values(
        offer_id=offer_id, city_id=city_id
    ).on_conflict_do_nothing(
        index_elements=["offer_id", "city_id"]
    )

    result = await db.execute(stmt)
    count = count_affected(result)
    await db.commit()
    return count


async def remove_city_from_offer(db: AsyncSession, offer_id: int, city_id: int):
    offer = await db.get(Offer, offer_id)
    if not offer:
        raise NoResultFound(f"Offer {offer_id} not found")

    city = await db.get(City, city_id)
    if not city:
        raise NoResultFound(f"City {city_id} not found")

    result = await db.execute(
        delete(offer_city).where(
            offer_city.c.offer_id == offer_id,
            offer_city.c.city_id  == city_id
        )
    )
    count = count_affected(result)
    await db.commit()
    return count

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

async def get_categories_by_name(
    db: AsyncSession,
    name_substr: str
) -> Sequence[Category]:
    stmt = (
        select(Category)
        .where(Category.name.ilike(f"%{name_substr}%"))
        .order_by(Category.name)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def delete_category(db: AsyncSession, category_id: int) -> int:
    linked = await count_offers_for_category(db, category_id)
    if linked > 0:
        raise ValueError(f"Категория {category_id} связана {linked} раз к предложению")
    result = await db.execute(delete(Category).where(Category.id == category_id))
    count = count_affected(result)
    await db.commit()
    return count

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

async def get_offers_by_title(
    db: AsyncSession,
    title_substr: str
) -> List[Offer]:
    stmt = (
        select(Offer)
        .where(Offer.title.ilike(f"%{title_substr}%"))
        .order_by(Offer.title)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def delete_offer(db: AsyncSession, offer_id: int) -> int:
    result = await db.execute(delete(Offer).where(Offer.id == offer_id))
    count = count_affected(result)
    await db.commit()
    return count

# --- Статистика ---

async def log_stat(db: AsyncSession, user_id: int, offer_id: int) -> Stat:
    stat = Stat(user_id=user_id, offer_id=offer_id)
    db.add(stat)
    await db.commit()
    await db.refresh(stat)
    return stat
