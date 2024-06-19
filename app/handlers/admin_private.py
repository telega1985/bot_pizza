from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.filters import Command, or_f
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters.chat_types import ChatTypeFilter, IsAdmin
from app.keyboards.inline import get_callback_btns
from app.keyboards.reply import get_reply_keyboard
from app.models.services import ProductService, CategoryService, BannerService

admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())


ADMIN_KB = get_reply_keyboard(
    "Добавить товар",
    "Ассортимент",
    "Добавить/Изменить баннер",
    placeholder="Выберите действие",
    sizes=(2,)
)


@admin_router.message(Command("admin"))
async def admin_features(message: Message):
    await message.answer("Что хотите сделать?", reply_markup=ADMIN_KB)


@admin_router.message(F.text == "Ассортимент")
async def assortment_of_categories(message: Message, session: AsyncSession):
    categories = await CategoryService.service_get_categories(session)
    btns = {category.name: f"category_{category.id}" for category in categories}
    await message.answer("Выберите категорию", reply_markup=get_callback_btns(btns=btns))


@admin_router.callback_query(F.data.startswith("category_"))
async def get_product_by_category(callback: CallbackQuery, session: AsyncSession):
    category_id = callback.data.split("_")[-1]

    products = await ProductService.service_get_all_products(session, int(category_id))

    for product in products:
        await callback.message.answer_photo(
            product.image,
            caption=f"<strong>{product.name}</strong>\n{product.description}\nСтоимость: {round(product.price, 2)}",
            reply_markup=get_callback_btns(
                btns={
                    "Удалить": f"delete_{product.id}",
                    "Изменить": f"change_{product.id}"
                }
            )
        )

    await callback.answer()
    await callback.message.answer("OK, вот список товаров ⤴")


@admin_router.callback_query(F.data.startswith("delete_"))
async def delete_product(callback: CallbackQuery, session: AsyncSession):
    product_id = callback.data.split("_")[-1]

    await ProductService.service_delete_product(session, int(product_id))

    await callback.answer()
    await callback.message.answer("Товар удален!")


############ FSM для загрузки/изменения баннеров #############


class AddBanner(StatesGroup):
    image = State()


@admin_router.message(F.text == "Добавить/Изменить баннер")
async def add_image_banner(message: Message, state: FSMContext, session: AsyncSession):
    banners = await BannerService.service_get_info_pages(session)
    pages_names = [page.name for page in banners]

    await message.answer(
        f"Отправьте фото баннера. \nВ описании укажите для какой страницы: \n{', '.join(pages_names)}"
    )
    await state.set_state(AddBanner.image)


@admin_router.message(AddBanner.image, F.photo)
async def add_banner(message: Message, state: FSMContext, session: AsyncSession):
    image = message.photo[-1].file_id
    name_page = message.caption.strip()
    banners = await BannerService.service_get_info_pages(session)
    pages_names = [page.name for page in banners]

    if name_page not in pages_names:
        await message.answer(f"Введите нормальное название страницы, например: \n{', '.join(pages_names)}")
        return

    await BannerService.service_change_banner_image(session, name_page, image)
    await message.answer("Баннер добавлен/изменен")
    await state.clear()


@admin_router.message(AddBanner.image)
async def incorrect_add_banner(message: Message):
    await message.answer("Отправьте фото баннера или отмена")


################## FSM для добавления/изменения товаров админом #####################


class AddProduct(StatesGroup):
    name = State()
    description = State()
    category = State()
    price = State()
    image = State()

    product_for_change = None

    texts = {
        "AddProduct:name": "Введите название заново",
        "AddProduct:description": "Введите описание заново",
        "AddProduct:category": "Выберите категорию заново",
        "AddProduct:price": "Введите стоимость заново",
        "AddProduct:image": "Этот стейт последний, поэтому..."
    }


@admin_router.callback_query(F.data.startswith("change_"))
async def change_product(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    product_id = callback.data.split("_")[-1]

    product_for_change = await ProductService.service_get_one_product(session, int(product_id))

    AddProduct.product_for_change = product_for_change
    await callback.answer()
    await callback.message.answer("Введите название товара", reply_markup=ReplyKeyboardRemove())

    await state.set_state(AddProduct.name)


@admin_router.message(F.text == "Добавить товар")
async def add_product(message: Message, state: FSMContext):
    await message.answer("Введите название товара", reply_markup=ReplyKeyboardRemove())
    await state.set_state(AddProduct.name)


@admin_router.message(or_f(Command("отмена"), F.text.casefold() == "отмена"))
async def cancel_handler(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()

    if current_state is None:
        return

    if AddProduct.product_for_change:
        AddProduct.product_for_change = None

    await state.clear()
    await message.answer("Действия отменены", reply_markup=ADMIN_KB)


@admin_router.message(or_f(Command("назад"), F.text.casefold() == "назад"))
async def back_handler(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()

    if current_state == AddProduct.name:
        await message.answer("Предыдущего шага нет. Или введите название товара или напишите 'отмена'")
        return

    previous = None

    for step in AddProduct.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(f"Ок, вы вернулись к прошлому шагу \n {AddProduct.texts[previous.state]}")

        previous = step


@admin_router.message(AddProduct.name, or_f(F.text, F.text == "."))
async def add_name(message: Message, state: FSMContext):
    if message.text == ".":
        await state.update_data(name=AddProduct.product_for_change.name)
    else:
        if len(message.text) >= 100:
            await message.answer("Название товара не должно превышать 100 символов. \n Введите заново")
            return

        await state.update_data(name=message.text)

    await message.answer("Введите описание товара")
    await state.set_state(AddProduct.description)


@admin_router.message(AddProduct.name)
async def incorrect_add_name(message: Message):
    await message.answer("Вы ввели недопустимые данные, введите текст названия товара")


@admin_router.message(AddProduct.description, or_f(F.text, F.text == "."))
async def add_description(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == ".":
        await state.update_data(description=AddProduct.product_for_change.description)
    else:
        await state.update_data(description=message.text)

    categories = await CategoryService.service_get_categories(session)
    btns = {category.name: str(category.id) for category in categories}
    await message.answer("Выберите категорию", reply_markup=get_callback_btns(btns=btns))

    await state.set_state(AddProduct.category)


@admin_router.message(AddProduct.description)
async def incorrect_add_description(message: Message):
    await message.answer("Вы ввели недопустимые данные, введите текст описания товара")


@admin_router.callback_query(AddProduct.category)
async def category_choice(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    categories = await CategoryService.service_get_categories(session)
    category_ids = [category.id for category in categories]

    if int(callback.data) in category_ids:
        await callback.answer()
        await state.update_data(category=callback.data)
        await callback.message.answer("Теперь введите цену товара")
        await state.set_state(AddProduct.price)
    else:
        await callback.message.answer("Выберите категорию из кнопок")
        await callback.answer()


@admin_router.callback_query(AddProduct.category)
async def incorrect_category_choice(message: Message):
    await message.answer("Выберите категорию из кнопок")


@admin_router.message(AddProduct.price, or_f(F.text, F.text == "."))
async def add_price(message: Message, state: FSMContext):
    if message.text == ".":
        await state.update_data(price=AddProduct.product_for_change.price)
    else:
        try:
            float(message.text)
        except ValueError:
            await message.answer("Введите корректное значение цены")
            return

        await state.update_data(price=message.text)

    await message.answer("Загрузите изображение товара")
    await state.set_state(AddProduct.image)


@admin_router.message(AddProduct.price)
async def incorrect_add_price(message: Message):
    await message.answer("Вы ввели недопустимые данные, введите стоимость товара")


@admin_router.message(AddProduct.image, or_f(F.photo, F.text == "."))
async def add_image(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == ".":
        await state.update_data(image=AddProduct.product_for_change.image)
    else:
        image = message.photo[-1].file_id
        await state.update_data(image=image)

    data = await state.get_data()

    try:
        if AddProduct.product_for_change:
            await ProductService.service_update_product(session, AddProduct.product_for_change.id, data)
        else:
            await ProductService.service_add_product(session, data)

        await message.answer("Товар добавлен/изменен", reply_markup=ADMIN_KB)
        await state.clear()
    except Exception as e:
        await message.answer(
            f"Ошибка: \n{str(e)}\n Обратитесь к программисту, он опять денег хочет", reply_markup=ADMIN_KB
        )
        await state.clear()

    AddProduct.product_for_change = None


@admin_router.message(AddProduct.image)
async def incorrect_add_image(message: Message):
    await message.answer("Отправьте фото пиццы")
