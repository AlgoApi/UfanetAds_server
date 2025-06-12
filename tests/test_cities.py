import pytest
from httpx import AsyncClient
from db.models import User, RoleEnum
from core.security import get_password_hash

@pytest.mark.asyncio
async def test_cities_crud(client: AsyncClient, db_session):
    # 1. Создаём пользователя-админа напрямую в БД
    hashed = get_password_hash("adminpass")
    admin = User(username="admin", hashed_password=hashed, role=RoleEnum.admin)
    db_session.add(admin)
    await db_session.commit()

    # 2. Получаем токен админа
    r = await client.post("/api/auth/token", data={"username": "admin", "password": "adminpass"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Добавляем город (OK)
    r2 = await client.post("/api/cities/", json={"name": "Moscow"}, headers=headers)
    assert r2.status_code == 201
    data = r2.json()
    assert data["name"] == "Moscow"
    city_id = data["id"]

    # 4. Снова добавляем такой же город → 400
    r3 = await client.post("/api/cities/", json={"name": "Moscow"}, headers=headers)
    assert r3.status_code == 400

    # 5. Пытаемся добавить город без токена → 401 или 403
    r4 = await client.post("/api/cities/", json={"name": "Saint-Petersburg"})
    assert r4.status_code in (401, 403)

    # 6. Получаем список городов (public endpoint)
    r5 = await client.get("/api/cities/")
    assert r5.status_code == 200
    arr = r5.json()
    assert isinstance(arr, list) and any(c["name"] == "Moscow" for c in arr)
