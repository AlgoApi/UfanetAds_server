from typing import Optional

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import uuid
from fastapi import Depends, Request, Response
from jose import JWTError, jwt
from sqlalchemy.exc import IntegrityError
from db.crud import create_user
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import get_db
from core.security import decode_access_token, create_access_token
from db.models import User, RoleEnum
from db.crud import get_user_by_username

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить учётные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    username: str | None = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = await get_user_by_username(db, username)
    if user is None:
        raise credentials_exception

    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user

async def get_or_create_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: AsyncSession = Depends(get_db), anon:bool = True
) -> User | dict | None:
    """
    Если есть валидный токен — возвращаем User.
    Если нет или он невалиден — создаём анонимного user и возвращаем:
      {"user": <User>, "token": "<новый_JWT>"}
    """
    if authorization:
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise ValueError()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        payload = decode_access_token(token)
        username: str | None = payload.get("sub")
        if username:
            user = await get_user_by_username(db, username)
            if user:
                return user

    # Если дошли до сюда — нет валидного токена или токен не нашёл пользователя
    # Создаём анона
    if anon:
        anon_username = f"anon_{uuid.uuid4()}"
        anon_password = uuid.uuid4().hex
        new_user = await create_user(db, anon_username, anon_password, RoleEnum.user)
        access_token = create_access_token({"sub": new_user.username, "role": new_user.role.value})
        return {"user": new_user, "token": access_token}
    return None


async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != RoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав (требуются права администратора)",
        )
    return current_user

async def get_current_superadmin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != RoleEnum.superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав (требуются права super)",
        )
    return current_user
