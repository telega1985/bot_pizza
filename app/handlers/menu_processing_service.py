from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.inline import get_user_main_btns, get_user_catalog_btns, get_products_btns, get_user_cart
from app.models.services import CartService, BannerService, ProductService, CategoryService
from app.utils.paginator import Paginator


class MenuProcessingService:
    @staticmethod
    async def main_menu(session: AsyncSession, level: int, menu_name: str):
        banner = await BannerService.service_get_banner(session, menu_name)
        image = InputMediaPhoto(media=banner.image, caption=banner.description)

        kbds = get_user_main_btns(level=level)

        return image, kbds

    @staticmethod
    async def catalog(session: AsyncSession, level: int, menu_name: str):
        banner = await BannerService.service_get_banner(session, menu_name)
        image = InputMediaPhoto(media=banner.image, caption=banner.description)
        categories = await CategoryService.service_get_categories(session)
        kbds = get_user_catalog_btns(level=level, categories=categories)

        return image, kbds

    @staticmethod
    def pages(paginator: Paginator):
        btns = dict()

        if paginator.has_previous():
            btns["◀ Пред."] = "previous"

        if paginator.has_next():
            btns["След. ▶"] = "next"

        return btns

    @classmethod
    async def products(cls, session: AsyncSession, level: int, category: int, page: int):
        products = await ProductService.service_get_all_products(session, category)

        paginator = Paginator(products, page=page)
        product = paginator.get_page()[0]

        image = InputMediaPhoto(
            media=product.image,
            caption=f"""
                    <strong>{product.name}</strong>\n{product.description}\nСтоимость: {round(product.price, 2)}\n
                    <strong>Товар {paginator.page} из {paginator.pages}</strong>
                    """
        )

        pagination_btns = cls.pages(paginator)

        kbds = get_products_btns(
            level=level,
            category=category,
            page=page,
            pagination_btns=pagination_btns,
            product_id=product.id
        )

        return image, kbds

    @classmethod
    async def carts(cls, session: AsyncSession, level: int, menu_name: str, page: int, user_id: int, product_id: int):
        if menu_name == "delete":
            await CartService.service_delete_from_cart(session, user_id, product_id)

            if page > 1:
                page -= 1

        elif menu_name == "decrement":
            is_cart = await CartService.service_reduce_product_in_cart(session, user_id, product_id)

            if page > 1 and not is_cart:
                page -= 1

        elif menu_name == "increment":
            await CartService.service_add_to_cart(session, user_id, product_id)

        carts = await CartService.service_get_user_carts(session, user_id)

        if not carts:
            banner = await BannerService.service_get_banner(session, "cart")
            image = InputMediaPhoto(
                media=banner.image, caption=f"<strong>{banner.description}</strong>"
            )

            kbds = get_user_cart(
                level=level,
                page=None,
                pagination_btns=None,
                product_id=None
            )
        else:
            paginator = Paginator(carts, page=page)

            cart = paginator.get_page()[0]

            cart_price = round(cart.quantity * cart.product.price, 2)
            total_price = round(sum(cart.quantity * cart.product.price for cart in carts), 2)
            image = InputMediaPhoto(
                media=cart.product.image,
                caption=f"""
                        <strong>{cart.product.name}</strong>\n{cart.product.price}$ x {cart.quantity} = {cart_price}$
                        \nТовар {paginator.page} из {paginator.pages} в корзине. \nОбщая стоимость товаров
                        в корзине {total_price}
                        """
            )

            pagination_btns = cls.pages(paginator)

            kbds = get_user_cart(
                level=level,
                page=page,
                pagination_btns=pagination_btns,
                product_id=cart.product.id
            )

        return image, kbds

    @classmethod
    async def get_menu_content(
            cls,
            session: AsyncSession,
            level: int,
            menu_name: str,
            category: int | None = None,
            page: int | None = None,
            product_id: int | None = None,
            user_id: int | None = None
    ):
        if level == 0:
            return await cls.main_menu(session, level, menu_name)
        elif level == 1:
            return await cls.catalog(session, level, menu_name)
        elif level == 2:
            return await cls.products(session, level, category, page)
        elif level == 3:
            return await cls.carts(session, level, menu_name, page, user_id, product_id)
