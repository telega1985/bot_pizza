from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.dao.base import BaseDAO
from app.models.models import Product, Banner, Category, User, Cart


class ProductDAO(BaseDAO):
    model = Product


class BannerDAO(BaseDAO):
    model = Banner


class CategoryDAO(BaseDAO):
    model = Category


class UserDAO(BaseDAO):
    model = User


class CartDAO(BaseDAO):
    model = Cart

    @classmethod
    async def db_get_user_carts(cls, session: AsyncSession, user_id: int):
        query = (
            select(cls.model)
            .options(joinedload(cls.model.product))
            .filter_by(user_id=user_id)
        )
        result = await session.execute(query)
        return result.scalars().all()
