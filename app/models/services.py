from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dao import ProductDAO, BannerDAO, CategoryDAO, UserDAO, CartDAO
from app.models.models import Product, Banner, Category, User, Cart


class ProductService:
    @classmethod
    async def service_add_product(cls, session: AsyncSession, data: dict):
        product = Product(
            name=data["name"],
            description=data["description"],
            price=float(data["price"]),
            image=data["image"],
            category_id=int(data["category"])
        )

        session.add(product)
        await session.commit()

    @classmethod
    async def service_get_all_products(cls, session: AsyncSession, category_id: int):
        return await ProductDAO.get_all(session, category_id=category_id)

    @classmethod
    async def service_get_one_product(cls, session: AsyncSession, product_id: int):
        return await ProductDAO.get_one(session, id=product_id)

    @classmethod
    async def service_update_product(cls, session: AsyncSession, product_id: int, data: dict):
        product = await cls.service_get_one_product(session, product_id)

        if product:
            for filed, value in data.items():
                setattr(product, filed, value)

            await session.commit()

    @classmethod
    async def service_delete_product(cls, session: AsyncSession, product_id: int):
        product = await cls.service_get_one_product(session, product_id)

        if product:
            await session.delete(product)

        await session.commit()


class BannerService:
    @classmethod
    async def service_add_banner(cls, session: AsyncSession, data: dict):
        banner = await BannerDAO.get_first(session)

        if not banner:
            banners = [Banner(name=name, description=description) for name, description in data.items()]
            session.add_all(banners)

        await session.commit()

    @classmethod
    async def service_change_banner_image(cls, session: AsyncSession, name: str, image: str):
        banner = await BannerDAO.get_one(session, name=name)

        if banner:
            banner.image = image

        await session.commit()

    @classmethod
    async def service_get_banner(cls, session: AsyncSession, page: str):
        return await BannerDAO.get_one(session, name=page)

    @classmethod
    async def service_get_info_pages(cls, session: AsyncSession):
        return await BannerDAO.get_all(session)


class CategoryService:
    @classmethod
    async def service_get_categories(cls, session: AsyncSession):
        return await CategoryDAO.get_all(session)

    @classmethod
    async def service_create_categories(cls, session: AsyncSession, categories: list):
        category = await CategoryDAO.get_first(session)

        if not category:
            categories_all = [Category(name=name) for name in categories]
            session.add_all(categories_all)

        await session.commit()


class UserService:
    @classmethod
    async def service_add_user(
            cls,
            session: AsyncSession,
            telegram_id: int,
            first_name: str | None = None,
            last_name: str | None = None,
            phone: str | None = None
    ):
        user = await UserDAO.get_one(session, telegram_id=telegram_id)

        if not user:
            db_user = User(
                telegram_id=telegram_id,
                first_name=first_name,
                last_name=last_name,
                phone=phone
            )
            session.add(db_user)
            await session.commit()


class CartService:
    @classmethod
    async def service_add_to_cart(cls, session: AsyncSession, user_id: int, product_id: int):
        cart = await CartDAO.get_one(session, user_id=user_id, product_id=product_id)

        if not cart:
            cart = Cart(user_id=user_id, product_id=product_id, quantity=1)
            session.add(cart)
        else:
            cart.quantity += 1

        await session.commit()

        return cart

    @classmethod
    async def service_get_user_carts(cls, session: AsyncSession, user_id: int):
        return await CartDAO.db_get_user_carts(session, user_id)

    @classmethod
    async def service_delete_from_cart(cls, session: AsyncSession, user_id: int, product_id: int):
        cart = await CartDAO.get_one(session, user_id=user_id, product_id=product_id)

        if cart:
            await session.delete(cart)

        await session.commit()

    @classmethod
    async def service_reduce_product_in_cart(cls, session: AsyncSession, user_id: int, product_id: int):
        cart = await CartDAO.get_one(session, user_id=user_id, product_id=product_id)

        if not cart:
            return False

        if cart.quantity > 1:
            cart.quantity -= 1
        else:
            await cls.service_delete_from_cart(session, user_id, product_id)

        await session.commit()

        return True
