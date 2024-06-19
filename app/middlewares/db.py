from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.common.texts_for_db import description_for_info_pages, categories
from app.models.services import BannerService, CategoryService


async def init_data(session: AsyncSession):
    await BannerService.service_add_banner(session, description_for_info_pages)
    await CategoryService.service_create_categories(session, categories)


class DataBaseSession(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        self.session_pool = session_pool

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        async with self.session_pool() as session:
            data["session"] = session

            await init_data(session)

            return await handler(event, data)
