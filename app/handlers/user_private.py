from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command, or_f
from aiogram.utils.formatting import as_list, as_marked_section, Bold
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.chat_types import ChatTypeFilter
from app.handlers.menu_processing_service import MenuProcessingService
from app.keyboards.inline import get_callback_btns, MenuCallback
from app.keyboards.reply import get_reply_keyboard
from app.models.services import ProductService, UserService, CartService

user_private_router = Router()
user_private_router.message.filter(ChatTypeFilter(["private"]))


@user_private_router.message(CommandStart())
async def start_cmd(message: Message, session: AsyncSession):
    media, reply_markup = await MenuProcessingService.get_menu_content(session, level=0, menu_name="main")

    await message.answer_photo(media.media, caption=media.caption, reply_markup=reply_markup)


async def add_to_cart(callback: CallbackQuery, callback_data: MenuCallback, session: AsyncSession):
    user = callback.from_user

    await UserService.service_add_user(
        session,
        telegram_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=None
    )

    await CartService.service_add_to_cart(session, user_id=user.id, product_id=callback_data.product_id)
    await callback.answer("Товар добавлен в корзину")


@user_private_router.callback_query(MenuCallback.filter())
async def user_menu(callback: CallbackQuery, callback_data: MenuCallback, session: AsyncSession):
    if callback_data.menu_name == "add_to_cart":
        await add_to_cart(callback, callback_data, session)
        return

    media, reply_markup = await MenuProcessingService.get_menu_content(
        session,
        level=callback_data.level,
        menu_name=callback_data.menu_name,
        category=callback_data.category,
        page=callback_data.page,
        product_id=callback_data.product_id,
        user_id=callback.from_user.id
    )

    await callback.message.edit_media(media=media, reply_markup=reply_markup)
    await callback.answer()



















# @user_private_router.callback_query(F.data.startswith("some_"))
# async def counter(callback: CallbackQuery):
#     number = int(callback.data.split("_")[-1])
#
#     await callback.message.edit_text(
#         text=f"Нажатий - {number}",
#         reply_markup=get_callback_btns(btns={"Нажми еще раз": f"some_{number + 1}"})
#     )





# USER_KB = get_reply_keyboard(
#     "Меню",
#     "О магазине",
#     "Варианты оплаты",
#     "Варианты доставки",
#     "Отправить номер ☎",
#     placeholder="Что вас интересует?",
#     request_contact=4
# )
#
#
# @user_private_router.message(CommandStart())
# async def start_cmd(message: Message):
#     await message.answer("Привет, я виртуальный помощник", reply_markup=USER_KB)
#
#
# @user_private_router.message(or_f(Command("menu"), F.text.lower() == "меню"))
# async def menu_cmd(message: Message, session: AsyncSession):
#     products = await ProductService.service_get_all_products(session)
#
#     for product in products:
#         await message.answer_photo(
#             product.image,
#             caption=f"<strong>{product.name}</strong>\n{product.description}\nСтоимость: {product.price}"
#         )
#
#     await message.answer("Вот меню:")
#
#
# @user_private_router.message(or_f(Command("about"), F.text.lower() == "о магазине"))
# async def about_cmd(message: Message):
#     await message.answer("О нас:")
#
#
# @user_private_router.message(or_f(Command("payment"), F.text.lower() == "варианты оплаты"))
# async def payment_cmd(message: Message):
#     text = as_marked_section(
#         Bold("Варианты оплаты:"),
#         "Картой в боте",
#         "При получении карта/кеш",
#         "В заведении",
#         marker="✅ "
#     )
#     await message.answer(text.as_html())
#
#
# @user_private_router.message(or_f(Command("shipping"), F.text.lower() == "варианты доставки"))
# async def shipping_cmd(message: Message):
#     text = as_list(
#         as_marked_section(
#             Bold("Варианты доставки/заказа:"),
#             "Курьер",
#             "Самовывоз",
#             "Покушаю у вас",
#             marker="✅ "
#         ),
#         as_marked_section(
#             Bold("Нельзя:"),
#             "Почта",
#             "Голуби",
#             marker="❌ "
#         ),
#         sep="\n--------------------------------\n"
#     )
#     await message.answer(text.as_html())
