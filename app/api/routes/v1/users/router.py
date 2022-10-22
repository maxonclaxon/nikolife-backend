from typing import Union

import sqlalchemy
from fastapi import Depends, Response, status, UploadFile, Form, File, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.routes.default_responses import DefaultResponse, UserRequestResponse, User, UserGoogleAuthResponse
from app.api.routes.v1.users.utility_classes import RegisterRequestModel, UserFromDB
from app.api.routes.v1.users.views.default import get_user_by_id_view, register_user_view, delete_user_view, \
    update_user_view, get_or_create_google_user_view
from app.api.routes.v1.utils.auth import get_current_active_user, get_password_hash
from app.database.manager import manager

from app.database.models.base import Users
from app.utils.s3_service import manager as s3_manager
from app.api.routes.v1.users.groups.router import router as groups_router

router = APIRouter(prefix="/users")
router.include_router(groups_router)


@router.get("/me", response_model=UserRequestResponse)
async def read_users_me(current_user: Users = Depends(get_current_active_user)):
    dicted = current_user.__dict__
    print(f"/me image: {current_user.image}")
    if current_user.image:
        dicted["image"] = s3_manager.get_url(current_user.image)
    return UserRequestResponse(detail="Пользователь найден", user=User(**dicted))


@router.get("/by_id/{user_id}", response_model=Union[UserRequestResponse, DefaultResponse])
async def get_user_by_id(
        user_id: int,
        session: AsyncSession = Depends(manager.get_session_object),
        current_user: Users = Depends(get_current_active_user)
) -> Users:
    return await get_user_by_id_view(user_id=user_id, session=session)


@router.post("/", response_model=DefaultResponse)
async def register_user(user: RegisterRequestModel, session: AsyncSession = Depends(manager.get_session_object)):
    return await register_user_view(user=user, session=session)

@router.get("/googleUser", response_model=UserGoogleAuthResponse)
async def get_or_create_google_user(
        token: str,
        session: AsyncSession = Depends(manager.get_session_object),
):

    return await get_or_create_google_user_view(token=token, session=session)


@router.delete("/", response_model=DefaultResponse)
async def delete_user(session: AsyncSession = Depends(manager.get_session_object),
                        current_user: Users = Depends(get_current_active_user)):
    return await delete_user_view(session=session, current_user=current_user)


@router.patch("/", response_model=DefaultResponse)
async def update_user(username=Form(default=None),
                      email=Form(default=None),
                      name=Form(default=None),
                      info=Form(default=None),
                      image: UploadFile = File(default=None),
                      session: AsyncSession = Depends(manager.get_session_object),
                      current_user: Users = Depends(get_current_active_user),
                      ):
    return await update_user_view(
        username=username,
        email=email,
        name=name,
        info=info,
        image=image,
        session=session,
        current_user=current_user
    )
