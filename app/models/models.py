from typing import Annotated, Optional

from sqlalchemy import String, Text, Numeric, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

intpk = Annotated[int, mapped_column(primary_key=True, index=True)]


class Banner(Base):
    __tablename__ = "banners"

    id: Mapped[intpk]
    name: Mapped[str] = mapped_column(String(15), unique=True)
    image: Mapped[Optional[str]] = mapped_column(String(150))
    description: Mapped[Optional[str]] = mapped_column(Text)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[intpk]
    name: Mapped[str] = mapped_column(String(150))

    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[intpk]
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Numeric(5, 2))
    image: Mapped[str] = mapped_column(String(150))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))

    category: Mapped["Category"] = relationship(back_populates="products")
    cart: Mapped["Cart"] = relationship(back_populates="product")


class User(Base):
    __tablename__ = "users"

    id: Mapped[intpk]
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(150))
    last_name: Mapped[Optional[str]] = mapped_column(String(150))
    phone: Mapped[Optional[str]] = mapped_column(String(13))

    cart: Mapped["Cart"] = relationship(back_populates="user")


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    quantity: Mapped[int]

    user: Mapped["User"] = relationship(back_populates="cart")
    product: Mapped["Product"] = relationship(back_populates="cart")
