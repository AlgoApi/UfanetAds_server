import pytest
from httpx import AsyncClient

from db.models import User, RoleEnum
from core.security import get_password_hash

@pytest.mark.asyncio
async def test_signup_and_login(client: AsyncClient, db_session):
    # 1. Регистрируемся
    signup_data = {"username": "testuser", "password": "strongpass"}
    r = await client.post("/api/auth/signup", json=signup_data)
    assert r.status_code == 200
    data = r.json()
    assert data["username"] == "testuser"
    assert data["role"] == "user"
    user_id = data["id"]

    # 2. Попробуем ещё раз зарегистрировать того же пользователя
    r2 = await client.post("/api/auth/signup", json=signup_data)
    assert r2.status_code == 400  # duplicate

    # 3. Логинимся
    login_data = {"username": "testuser", "password": "strongpass"}
    r3 = await client.post("/api/auth/token", data=login_data)
    assert r3.status_code == 200
    token_data = r3.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # 4. Некорректный логин/пароль
    r4 = await client.post("/api/auth/token", data={"username": "wrong", "password": "wrong"})
    assert r4.status_code == 401
