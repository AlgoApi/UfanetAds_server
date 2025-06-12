import pytest
from httpx import AsyncClient

from core.security import get_password_hash
from db.models import User, RoleEnum

@pytest.mark.asyncio
async def test_category_and_offer_validation(client: AsyncClient, db_session):
    # Создаём админа
    hashed = get_password_hash("adminpass")
    admin = User(username="admin2", hashed_password=hashed, role=RoleEnum.admin)
    db_session.add(admin)
    await db_session.commit()

    r = await client.post("/api/auth/token", data={"username": "admin2", "password": "adminpass"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Попробуем создать категорию без imageUrl → 422
    r_bad_cat = await client.post("/api/categories/", json={
        "name": "BadCat"
    }, headers=headers)
    assert r_bad_cat.status_code == 422

    # Попробуем создать категорию с некорректным URL → 422
    r_bad_cat2 = await client.post("/api/categories/", json={
        "name": "BadCat2",
        "image_url": "not_a_url"
    }, headers=headers)
    assert r_bad_cat2.status_code == 422

    # Создаём корректную категорию
    r_cat = await client.post("/api/categories/", json={
        "name": "GoodCat",
        "image_url": "https://example.com/cat.png"
    }, headers=headers)
    assert r_cat.status_code == 201
    cat_id = r_cat.json()["id"]

    # Создаём город
    r_city = await client.post("/api/cities/", json={"name": "GoodCity"}, headers=headers)
    city_id = r_city.json()["id"]

    # Попробуем создать предложение без backgroundImageUrl → 422
    r_bad_off = await client.post("/api/offers/", json={
        "title": "BadOffer",
        "description": "Desc",
        "cities_ids": [city_id],
        "categories_ids": [cat_id],
        "company_logo_url": "https://example.com/logo.png",
        "company_name": "Comp"
    }, headers=headers)
    assert r_bad_off.status_code == 422

    # Попробуем с некорректным URL → 422
    r_bad_off2 = await client.post("/api/offers/", json={
        "title": "BadOffer2",
        "description": "Desc",
        "cities_ids": [city_id],
        "categories_ids": [cat_id],
        "background_image_url": "ftp://wrong.com",
        "company_logo_url": "not_a_url",
        "company_name": "Comp"
    }, headers=headers)
    assert r_bad_off2.status_code == 422

    # Создаём корректное предложение
    r_off = await client.post("/api/offers/", json={
        "title": "GoodOffer",
        "description": "Desc",
        "cities_ids": [city_id],
        "categories_ids": [cat_id],
        "background_image_url": "https://example.com/bg.png",
        "company_logo_url": "https://example.com/logo.png",
        "company_name": "Comp"
    }, headers=headers)
    data = r_off.json()
    assert r_off.status_code == 201
    assert data["company_name"] == "Comp"
    assert data["background_image_url"].startswith("https://")
