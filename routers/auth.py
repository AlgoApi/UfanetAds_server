from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm

from db.dependencies import get_db, get_current_active_user, get_or_create_user
from db.crud import get_user_by_username, create_user
from core.security import verify_password, create_access_token
from db.models import User
from schemas.user import UserRead, UserCreate, Token, RoleEnum

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=UserRead, summary="Регистрация нового пользователя")
async def signup(user_data: UserCreate, db: AsyncSession = Depends(get_db),
                 authorization: Optional[str] = Header(None, alias="Authorization")):
    """
    Регистрация пользователя. Новые пользователи по умолчанию получают роль 'user'.
    """
    is_super = False

    current_user_data = await get_or_create_user(authorization=authorization, db=db, anon=False)

    existing_user = await get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Имя уже занято")

    if isinstance(current_user_data, User):
        current_user: User = current_user_data
        is_super = current_user.role == RoleEnum.superadmin

    user = await create_user(db, user_data.username, user_data.password, RoleEnum.admin if is_super else RoleEnum.user)

    return user


@router.post("/token", response_model=Token, summary="Получение JWT по логину и паролю")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    #Возвращает JWT, если логин/пароль верные.
    user = await get_user_by_username(db, form_data.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверные учётные данные")
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверные учётные данные")
    token = create_access_token(
        data={"sub": user.username, "role": user.role.value}
    )
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserRead, summary="Информация о текущем пользователе")
async def read_users_me(current_user=Depends(get_current_active_user)):
    return current_user
