# tests/test_offers_router.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_offers_crud_and_relations_and_search(client: AsyncClient):
    # Подготовим 2 города и 2 категории
    r_c1 = await client.post("/api/categories/", json={"name":"Cat1","image_url":"https://example.com/u"}, headers={"X-ADMIN":"1"})
    c1 = r_c1.json()
    cid1 = c1["id"]
    r_c2 = await client.post("/api/categories/", json={"name":"Cat2","image_url":"https://example.com/u"}, headers={"X-ADMIN":"1"})
    cid2 = r_c2.json()["id"]

    r_city1 = await client.post("/api/cities/", json={"name":"CityA"})
    city1 = r_city1.json()
    city_id = city1["id"]
    r_city2 = await client.post("/api/cities/", json={"name":"CityB"})
    city_id2 = r_city2.json()["id"]
    r_city3 = await client.post("/api/cities/", json={"name": "CityC"})
    city_id3 = r_city3.json()["id"]

    # 1) Добавить оффер background_image_url company_logo_url company_name cities_ids categories_ids
    offer_payload = {
      "title":"OfferX","description":"Desc",
      "background_image_url":"https://example.com/u","company_logo_url":"https://example.com/l","company_name":"Comp",
      "cities_ids":[city_id, city_id2],
      "categories_ids":[cid1]
    }
    r1 = await client.post("/api/offers/", json=offer_payload, headers={"X-ADMIN":"1"})
    assert r1.status_code == 201
    offer = r1.json(); oid = offer["id"]
    assert offer["title"] == "OfferX"

    # 2) GET /api/offers/?city_id=CityA возвращает наш оффер
    r2 = await client.get(f"/api/offers/?city_id={city_id}")
    assert r2.status_code == 200
    items = r2.json()
    assert any(o["id"] == oid for o in items)

    # 3) Добавить существующую связь city → оффер => 404
    r3 = await client.post(f"/api/offers/{oid}/cities/{city_id}", headers={"X-ADMIN":"1"})
    assert r3.status_code == 404

    # 3) Добавить новую связь city → оффер => 200
    r3 = await client.post(f"/api/offers/{oid}/cities/{city_id3}", headers={"X-ADMIN": "1"})
    assert r3.status_code == 200 and r3.json() == 1

    # 6) Удалить связь оффер←city
    r6 = await client.delete(f"/api/offers/{oid}/cities/{city_id}", headers={"X-SUPER":"1"})
    assert r6.status_code == 200 and r6.json() == 1

    # 7) Удалить оффер
    r7 = await client.delete(f"/api/offers/{oid}", headers={"X-SUPER":"1"})
    assert r7.status_code == 200 and r7.json() == 1

    # 8) Поиск по части заголовка
    # создаём ещё два
    await client.post("/api/offers/", json={**offer_payload, "title":"FooBar"}, headers={"X-ADMIN":"1"})
    await client.post("/api/offers/", json={**offer_payload, "title":"BarBaz"}, headers={"X-ADMIN":"1"})
    r8 = await client.get("/api/offers/search?title=Bar")
    assert r8.status_code == 200
    found = r8.json()
    assert len(found) >= 2

    r9 = await client.get("/api/categories/search?title=Cat2")
    assert r9.status_code == 200
    found = r9.json()
    assert len(found) > 0

    r10 = await client.get("/api/cities/search?title=CityA")
    assert r10.status_code == 200
    found = r10.json()
    assert len(found) > 0
