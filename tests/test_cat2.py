# tests/test_categories_router.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_categories_crud_and_search(client: AsyncClient):
    # 1) Список пуст
    r0 = await client.get("/api/categories/")
    assert r0.status_code == 200
    assert r0.json() == []

    # 2) Создание категории
    payload = {"name": "Food", "image_url": "http://img/food.png"}
    r1 = await client.post("/api/categories/", json=payload, headers={"X-ADMIN":"1"})
    assert r1.status_code == 201
    cat = r1.json()
    assert cat["name"] == "Food"
    cat_id = cat["id"]

    # 3) Повтор создания => 400
    r1b = await client.post("/api/categories/", json=payload, headers={"X-ADMIN":"1"})
    assert r1b.status_code == 400

    # 4) Поиск по подстроке
    r2 = await client.get("/api/categories/search?title=Fo")
    assert r2.status_code == 200
    found = r2.json()
    assert any(c["id"] == cat_id for c in found)

    # 5) Удалить категорию, пока нет offers => OK
    r3 = await client.delete(f"/api/categories/{cat_id}", headers={"X-SUPER":"1"})
    assert r3.status_code == 200
    assert r3.json() == 1

    # 6) Удалить несуществующую => 404
    r4 = await client.delete(f"/api/categories/{cat_id}", headers={"X-SUPER":"1"})
    assert r4.status_code == 404
