# tests/test_auth_router.py
import pytest
from httpx import AsyncClient
from schemas.user import UserCreate, Token

@pytest.mark.asyncio
async def test_signup_and_login(client: AsyncClient):
    # 1) Регистрация нового юзера
    r = await client.post(
        "/api/auth/signup",
        json={"username": "alice", "password": "secret"}
    )
    assert r.status_code == 200
    data = r.json()
    assert data["username"] == "alice"
    assert data["role"] == "user"
    user_id = data["id"]

    # 2) Повторная регистрация => 400
    r2 = await client.post(
        "/api/auth/signup",
        json={"username": "alice", "password": "secret"}
    )
    assert r2.status_code == 400

    # 3) Получение токена с правильными данными
    # FastAPI ожидает form с grant_type=password
    r3 = await client.post(
        "/api/auth/token",
        data={"grant_type": "password", "username":"alice","password":"secret"}
    )
    assert r3.status_code == 200
    token_data = Token.model_validate(r3.json())
    assert token_data.token_type == "bearer"
    assert token_data.access_token

    # 4) Неправильный логин/пароль => 401
    r4 = await client.post(
        "/api/auth/token",
        data={"grant_type":"password","username":"alice","password":"wrong"}
    )
    assert r4.status_code == 401

    # 5) /me возвращает данные
    headers = {"Authorization": f"Bearer {token_data.access_token}"}
    r5 = await client.get("/api/auth/me", headers=headers)
    assert r5.status_code == 200
    me = r5.json()
    assert me["username"] == "alice"
