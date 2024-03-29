"""
Views for user routes
"""
import asyncio
import datetime
import uuid
from datetime import timedelta
from io import BytesIO
from typing import Optional, List

import requests
import sqlalchemy
from fastapi import HTTPException, Form, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from app.api.routes.default_response_models import DefaultResponse, UserRequestResponse, User, UserAuthResponse, \
    UsersRequestResponse
from app.api.routes.v1.groups.utils import get_group_model_or_create_if_not_exists
from app.api.routes.v1.users.models import RegisterRequestModel
from app.api.routes.v1.utils.auth import get_user_by_token, get_password_hash
from app.api.routes.v1.utils.service_models import UserModel
from app.api.routes.v1.utils.utility import build_full_path
from app.constants import DEFAULT_USER_GROUP_NAME, ADMIN_GROUP_NAME
from app.database import DatabaseManagerAsync
from app.database.models.base import Users, association_users_groups, Groups
from app.utils import S3Manager
from app.utils.auth import AvailableAuthProviders, AppleAuthentication, GoogleAuthentication, AuthBase


async def get_user_by_id_view(
        user_id: int,
        session: AsyncSession
) -> UserRequestResponse:
    """
    View for get user by id route (GET .../users/by_id/{user_id})

    :param user_id: user id.
    :param session: SQLAlchemy session object.
    :return: Response with user object
    """
    async with session.begin():
        user: Users = await Users.get_by_id(user_id=user_id, session=session, join_tables=[Users.groups])
        dicted = user.__dict__
        if user.image:
            # if user has a profile image, then we should get its link from s3
            dicted["image"] = S3Manager.get_instance().get_url(f"{user.image}_small.jpg")
        del dicted["groups"]
        user_response = UserRequestResponse(detail="Пользователь найден", user=User(**dicted))
        user_response.user.groups = await Users.get_groups_with_expiration_time(user_id=user.id, session=session)
        return user_response


async def get_all_users_view(session: AsyncSession) -> UsersRequestResponse:
    """
    View for get all users

    :param session: SQLAlchemy session object.
    :return: Response with users list
    """
    async with session.begin():
        users = await Users.get_all(session=session, join_tables=[Users.groups])
        users = [user.__dict__ for user in users]
        for user in users:
            user["groups"] = await Users.get_groups_with_expiration_time(user_id=user["id"], session=session)
        return UsersRequestResponse(detail="Пользователи найдены", users=[User(**user) for user in users])


async def authenticate_by_provider_view(
        token: str,
        provider: AvailableAuthProviders,
        session: AsyncSession,
) -> UserAuthResponse:
    """
    View gets user object by passed token with selected auth provider

    :param token: Authentication token
    :param provider: Authentication provider type
    :param session: SQLAlchemy AsyncSession object
    :return: user object
    """

    async with session.begin():
        if provider == AvailableAuthProviders.APPLE:
            user = await AppleAuthentication().authenticate(token=token, session=session)
        elif provider == AvailableAuthProviders.GOOGLE:
            user = await GoogleAuthentication().authenticate(token=token, session=session)
        else:
            raise HTTPException(
                detail=f"Не найден провайдер {provider} для аутентификации",
                status_code=404,
            )
        dicted = user.__dict__.copy()
        if user.image:
            dicted["image"] = S3Manager.get_instance().get_url(f"{user.image}_small.jpg")
        dicted["groups"] = await Users.get_groups_with_expiration_time(user_id=user.id, session=session)
        return UserAuthResponse(detail="Пользователь найден", user=User(**dicted), jwt=await AuthBase.generate_jwt(user=user))


async def register_user_view(
        user: RegisterRequestModel,
        session: AsyncSession
) -> DefaultResponse:
    """
    View for register a new user route (POST .../users/)
    :param user:
    :param session:
    :return:
    """
    async with session.begin():
        stmt = sqlalchemy.select(Users).where(Users.username == user.username)
        resp = await session.execute(stmt)
        found_user = resp.fetchall()
        if found_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Пользователь с таким ником уже зарегистрирован")
        user.password = get_password_hash(user.password)
        user.username = user.email
        new_user = Users(**user.dict())
        new_user.groups.append(await get_group_model_or_create_if_not_exists(group_name=DEFAULT_USER_GROUP_NAME,
                                                                             session=session))
        session.add(new_user)
        await session.commit()
        return DefaultResponse(detail="Регистрация успешна")


async def delete_user_view(
        session: AsyncSession,
        current_user: UserModel
) -> DefaultResponse:
    """
    View for delete user route.

    :param session: SQLAlchemy AsyncSession object
    :param current_user: User information object
    :return: Response with status
    """
    # TODO: change get_by_username to get_by_id (requires frontend changes)
    user_to_delete = current_user
    async with session.begin():
        user: Users = await Users.get_by_username(
            session=session,
            username=user_to_delete.username,
            join_tables=[Users.created_recipes]
        )
        for recipe in user.created_recipes:
            await session.delete(recipe)
        await session.delete(user)
        return DefaultResponse(detail=f"Пользователь с ником '{user_to_delete.username}' удален из приложения")


async def update_user_view(
        session: AsyncSession,
        current_user: UserModel,
        username=Form(default=None),
        email=Form(default=None),
        name=Form(default=None),
        info=Form(default=None),
        groups=Form(default=None),
        image: UploadFile = File(default=None),
                           ):
    """
    View for update user information router

    :param username: new username (optional).
    :param email: new email (optional).
    :param name: new name (optional).
    :param info: new info (optional).
    :param groups: new user groups (optional).
    :param image: new image (optional).
    :param session: SQLAlchemy AsyncSession object.
    :param current_user: User information object.
    :return: Response with status
    """

    async with session.begin():
        # TODO: change get_by_username to get_by_id (requires frontend changes)
        if ADMIN_GROUP_NAME not in current_user.groups and username!=current_user.username:
            raise HTTPException(status_code=403, detail="Вам нельзя редактировать этого пользователя")
        user: Users = await Users.get_by_username(session=session, username=username, join_tables=[Users.groups])
        if username:
            user.username = username
        if email:
            user.email = email
        if name:
            user.name = name
        if info:
            user.info = info
        if image:
            filename = build_full_path(f"{user.email}/avatar", image)
            S3Manager.get_instance().send_image_shaped(image=image, base_filename=filename)
            user.image = filename
        if groups:
            groups = eval(groups.replace("null", "None"))

            new_user_groups = []
            for group in groups:
                group["expiration_time"] = datetime.datetime.strptime(group["expiration_time"], "%Y-%m-%d") if group["expiration_time"] else None
                new_user_groups.append(await get_group_model_or_create_if_not_exists(group["name"], session))
            user.groups = new_user_groups
            user_id = user.id
            await session.commit()
            async with DatabaseManagerAsync.get_instance().get_session() as temp_session:
                for group in groups:
                    if group["expiration_time"] is None:
                        continue
                    tmp = await get_group_model_or_create_if_not_exists(group["name"], temp_session)
                    await Groups.update_expiration_time(
                        user_id=user_id,
                        group_id=tmp.id,
                        expiration_time=group["expiration_time"],
                        session=temp_session
                    )
        return DefaultResponse(detail="Информация о пользователе обновлена")
