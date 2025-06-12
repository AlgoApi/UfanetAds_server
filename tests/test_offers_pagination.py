import pytest
from httpx import AsyncClient

from core.security import get_password_hash
from db.models import User, RoleEnum, City, Category, Offer

@pytest.mark.asyncio
async def test_offers_pagination_and_new_fields(client: AsyncClient, db_session):
    # 1. Создаём админа
    hashed = get_password_hash("adminpass")
    admin = User(username="admin", hashed_password=hashed, role=RoleEnum.admin)
    db_session.add(admin)
    await db_session.commit()

    # 2. Логинимся
    r = await client.post("/api/auth/token", data={"username": "admin", "password": "adminpass"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Создаём город и категорию
    r_c = await client.post("/api/cities/", json={"name": "TestCity"}, headers=headers)
    city_id = r_c.json()["id"]
    r_cat = await client.post("/api/categories/", json={
        "name": "TestCategory",
        "image_url": "https://example.com/cat.png"
    }, headers=headers)
    cat_id = r_cat.json()["id"]

    # 4. Создадим 7 предложений, каждое со всеми обязательными полями
    for i in range(1, 8):
        payload = {
            "title": f"Offer{i}",
            "description": f"Desc {i}",
            "cities_ids": [city_id],
            "categories_ids": [cat_id],
            "background_image_url": "https://example.com/bg.png",
            "company_logo_url": "https://example.com/logo.png",
            "company_name": f"Company{i}"
        }
        r_off = await client.post("/api/offers/", json=payload, headers=headers)
        assert r_off.status_code == 201

    # 5. Запрашиваем first page (offset=0)
    r_page1 = await client.get(f"/api/offers/?offset=0&city_id={city_id}&category_id={cat_id}")
    assert r_page1.status_code == 200
    arr1 = r_page1.json()
    assert len(arr1) == 5
    for item in arr1:
        assert item["companyLogoUrl"].startswith("https://")
        assert item["companyName"].startswith("Company")

    # 6. Запрашиваем second page (offset=5)
    r_page2 = await client.get(f"/api/offers/?offset=5&city_id={city_id}&category_id={cat_id}")
    assert r_page2.status_code == 200
    arr2 = r_page2.json()
    # Должно быть 2 элемента (7−5=2)
    assert len(arr2) == 2

    # 8. offset < 0 тоже 422
    r_bad2 = await client.get(f"/api/offers/?offset=-1&city_id={city_id}&category_id={cat_id}")
    assert r_bad2.status_code == 422
