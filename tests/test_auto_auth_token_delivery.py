import pytest
from httpx import AsyncClient

from db.models import User, RoleEnum
from core.security import get_password_hash

@pytest.mark.asyncio
async def test_auto_auth_token_delivery(client: AsyncClient, db_session):
    """
    Проверяем, что при отсутствии токена клиенту выдаётся Authorization в заголовке ответа (или x-access-token).
    """
    # Сначала добавим пару записей для того, чтобы GET /offers вернул что-нибудь
    hashed = get_password_hash("adminpass")
    admin = User(username="admin3", hashed_password=hashed, role=RoleEnum.admin)
    db_session.add(admin)
    await db_session.commit()

    # Логинимся
    r = await client.post("/api/auth/token", data={"username": "admin3", "password": "adminpass"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Создаём город и категорию
    r_city = await client.post("/api/cities/", json={"name": "CityA"}, headers=headers)
    city_id = r_city.json()["id"]
    r_cat = await client.post("/api/categories/", json={
        "name": "CatA",
        "image_url": "https://example.com/cat.png"
    }, headers=headers)
    cat_id = r_cat.json()["id"]

    # Создаём предложение
    r_off = await client.post("/api/offers/", json={
        "title": "OffA",
        "description": "Desc",
        "cities_ids": [city_id],
        "categories_ids": [cat_id],
        "background_image_url": "https://example.com/bg.png",
        "company_logo_url": "https://example.com/logo.png",
        "company_name": "CompA"
    }, headers=headers)
    log = r_off.json()
    assert r_off.status_code == 201

    # Теперь делаем GET /api/offers без токена. Должны получить список + заголовок x-access-token
    r_list = await client.get("/api/offers/", params={"offset": 0, "city_id": city_id, "category_id": cat_id})
    assert r_list.status_code == 200
    # Проверяем, что заголовок x-access-token присутствует
    assert "x-access-token" in r_list.headers
    new_token = r_list.headers["x-access-token"]
    assert new_token.startswith("eyJ")  # JWT начинается с eyJ...
    log = r_list.json()
    assert log[0]["backgroundImageUrl"] == "https://example.com/bg.png"

    # Второй раз с тем же токеном — не должно быть нового токена
    r_list2 = await client.get("/api/offers/", params={"offset": 0, "city_id": city_id, "category_id": cat_id}, headers={"Authorization": f"Bearer {new_token}"})
    assert r_list2.status_code == 200
    assert "x-access-token" not in r_list2.headers
    log = r_list2.json()
    assert log[0]["companyLogoUrl"] == "https://example.com/logo.png"
