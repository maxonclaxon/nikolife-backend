"""
In this module admin panel is initializing with sqladmin package.
Check https://github.com/aminalaee/sqladmin
"""

from datetime import timedelta

import fastapi
from fastapi import HTTPException
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from app.api.routes.v1.users.utils import get_user_by_id
from app.api.routes.v1.utils.auth import authenticate_user, create_access_token
from app.config import settings
from app.constants import ACCESS_TOKEN_EXPIRE_MINUTES, ADMIN_GROUP_NAME
from app.database.models.base import (
    Users, Groups, IngredientsGroups, Recipes, Ingredients, RecipeDimensions,
    RecipeIngredients, RecipeCategories, RecipeCompilations, Story, Articles)
from app.database import DatabaseManagerAsync


class MyBackend(AuthenticationBackend):
    """Backend for admin panel"""
    async def login(self, request: Request) -> bool:
        """admin authenticate method"""
        async with DatabaseManagerAsync.get_instance().get_session() as session:
            form = await request.form()
            user = await authenticate_user(form["username"], form["password"])
            user = await get_user_by_id(user_id=user.id, session=session)
            if ADMIN_GROUP_NAME not in [group.name for group in user.groups]:
                raise HTTPException(status_code=401, detail="Not admin")
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                username=user.username, expires_delta=access_token_expires
            )

            # Validate username/password credentials
            # And update session
            request.session.update({"token": access_token})
            return True

    async def logout(self, request: Request) -> bool:
        """Admin log out method"""
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        """"""
        return "token" in request.session


def create_admin(app: fastapi.FastAPI):
    """Method initializes admin panel."""
    admin = Admin(
        app,
        DatabaseManagerAsync.get_instance().get_engine(),
        authentication_backend=MyBackend(secret_key=settings.api.secret_key)
    )

    class UsersPanel(ModelView, model=Users):
        """Users panel"""
        name = "????????????????????????"
        name_plural = "????????????????????????"
        column_list = [Users.id, Users.username, Users.name, Users.info, Users.groups]
        icon = "fa-solid fa-user"

    class GroupsPanel(ModelView, model=Groups):
        """Users groups panel"""
        name = "????????????"
        name_plural = "???????????? ??????????????????????????"
        column_list = [Groups.id, Groups.name]

    class IngredientGroupsPanel(ModelView, model=IngredientsGroups):
        """Ingredients groups panel"""
        name = "???????????? ????????????????????????"
        name_plural = "???????????? ????????????????????????"
        column_list = [IngredientsGroups.id, IngredientsGroups.name]

    class RecipesPanel(ModelView, model=Recipes):
        """Recipes panel"""
        name = "????????????"
        name_plural = "??????????????"
        column_list = [Recipes.id, Recipes.title]

    class IngredientsPanel(ModelView, model=Ingredients):
        """Ingredients panel"""
        name = "????????????????????"
        name_plural = "??????????????????????"
        column_list = [Ingredients.id, Ingredients.name, Ingredients.groups]

    class RecipeDimensionsPanel(ModelView, model=RecipeDimensions):
        """Recipe dimensions panel"""
        name = "?????????????????????? (?????? / ??????????)"
        name_plural = "?????????????????????? (?????? / ??????????)"
        column_list = [RecipeDimensions.id, RecipeDimensions.name]

    class RecipeIngredientsPanel(ModelView, model=RecipeIngredients):
        """Recipe ingredients panel"""
        name = "?????????? ????????????-????????????????????"
        name_plural = "?????????? ????????????-????????????????????"
        column_list = [
            RecipeIngredients.id, RecipeIngredients.recipe_id,
            RecipeIngredients.dimension, RecipeIngredients.ingredient
        ]

    class RecipeCategoriesPanel(ModelView, model=RecipeCategories):
        """Recipe categories panel"""
        name = "??????????????????"
        name_plural = "??????????????????"
        column_list = [RecipeCategories.id, RecipeCategories.name]

    class RecipeCompilationsPanel(ModelView, model=RecipeCompilations):
        """Recipe compilations panel"""
        name = "????????????????"
        name_plural = "????????????????"
        column_list = [RecipeCompilations.id, RecipeCompilations.name]

    class StoryPanel(ModelView, model=Story):
        """Story panel"""
        name = "??????????????"
        name_plural = "??????????????"
        column_list = [Story.id, Story.title]

    class ArticlePanel(ModelView, model=Articles):
        """Article panel"""
        name = "??????????????"
        name_plural = "??????????????"
        column_list = [Articles.id, Articles.title]

    admin.add_view(UsersPanel)
    admin.add_view(GroupsPanel)
    admin.add_view(IngredientGroupsPanel)
    admin.add_view(RecipesPanel)
    admin.add_view(IngredientsPanel)
    admin.add_view(RecipeDimensionsPanel)
    admin.add_view(RecipeIngredientsPanel)
    admin.add_view(RecipeCategoriesPanel)
    admin.add_view(RecipeCompilationsPanel)
    admin.add_view(StoryPanel)
    admin.add_view(ArticlePanel)
