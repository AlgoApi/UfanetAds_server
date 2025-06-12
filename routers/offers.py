import json

from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from fastapi.responses import JSONResponse
from db.dependencies import get_db, get_current_active_user, get_current_admin_user, get_or_create_user
from db.crud import get_offers_by_city_and_category, create_offer, log_stat
from schemas.category import CategoryRead
from schemas.offer import OfferCreate, OfferRead
from db.models import Offer, User

router = APIRouter(prefix="/api/offers", tags=["offers"])


@router.get("/", response_model=List[OfferRead], summary="Получение рекламных предложений")
async def read_offers(
        authorization: Optional[str] = Header(None, alias="Authorization"),
        offset: int = Query(0, ge=0),
        city_id: Optional[int] = None,
        category_id: Optional[int] = None,
        db: AsyncSession = Depends(get_db),
):
    """
    Если пользователь авторизован иначе создаём анонимуса
    """

    current_user_data = await get_or_create_user(authorization=authorization, db=db)

    if isinstance(current_user_data, dict):
        current_user: User = current_user_data["user"]
        new_token: str = current_user_data["token"]
        send_token = True
    else:
        current_user: User = current_user_data
        new_token = None
        send_token = False

    limit = 5
    offers = await get_offers_by_city_and_category(db, city_id, category_id, limit=limit, offset=offset)

    # Логируем статистику: для каждого предложения делаем запись
    #for offer in offers:
    #    await log_stat(db, current_user.id, offer.id)

    response_offers: list[OfferRead] = []
    for offer_obj in offers:
        offer_data = OfferRead.model_validate(offer_obj)
        #if category_obj:
        #    offer_data.category = CategoryRead.model_validate(category_obj)
        response_offers.append(offer_data)
    payload = [item.model_dump(mode="json") for item in response_offers]
    if send_token:
        headers = {"x-access-token": new_token}
        return JSONResponse(content=payload, headers=headers)

    return JSONResponse(content=payload)


@router.post("/", response_model=OfferRead, status_code=status.HTTP_201_CREATED, summary="Добавление нового предложения")
async def add_offer(
    offer_in: OfferCreate,
    db: AsyncSession = Depends(get_db),
    current_admin=Depends(get_current_admin_user)
):
    """
    Только администратор может добавлять рекламные предложения.
    """
    try:
        new_offer = await create_offer(
            db,
            title=offer_in.title,
            description=offer_in.description,
            cities_ids=offer_in.cities_ids,
            categories_ids=offer_in.categories_ids,
            background_image_url=offer_in.backgroundImageUrl,
            company_logo_url=offer_in.companyLogoUrl,
            company_name=offer_in.companyName
        )

        offer_data = OfferRead.model_validate(new_offer)
        return offer_data
    #except Exception:
    #    raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Ошибка при создании предложения")
    finally:
        pass
