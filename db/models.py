from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Enum, Table, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from db.base import Base
import enum
import uuid

# Перечисление ролей
class RoleEnum(str, enum.Enum):
    user = "user"
    admin = "admin"
    superadmin = "superadmin"

# Промежуточная таблица для связи Offer и City
offer_city = Table(
    'offer_city', Base.metadata,
    Column('offer_id', ForeignKey('offers.id', ondelete='CASCADE'), primary_key=True),
    Column('city_id', ForeignKey('cities.id', ondelete='CASCADE'), primary_key=True)
)

offer_category = Table(
    'offer_category', Base.metadata,
    Column('offer_id', ForeignKey('offers.id', ondelete='CASCADE'), primary_key=True),
    Column('category_id', ForeignKey('categories.id', ondelete='CASCADE'), primary_key=True)
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[RoleEnum] = mapped_column(
        Enum(RoleEnum),
        default=RoleEnum.user,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    stats: Mapped[list["Stat"]] = relationship(back_populates="user")


class City(Base):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    offers: Mapped[list["Offer"]] = relationship(
        'Offer', secondary=offer_city, back_populates='cities'
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    imageUrl: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    offers: Mapped[list["Offer"]] = relationship(
        'Offer', secondary=offer_category, back_populates='categories'
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    background_image_url: Mapped[str] = mapped_column(String(200), nullable=False)
    company_logo_url: Mapped[str] = mapped_column(String(200), nullable=False)
    company_name: Mapped[str] = mapped_column(String(100), nullable=False)

    cities: Mapped[list[City]] = relationship(
        'City', secondary=offer_city, back_populates='offers'
    )
    categories: Mapped[list[Category]] = relationship(
        'Category', secondary=offer_category, back_populates='offers'
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class Stat(Base):
    __tablename__ = "stats"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    offer_id: Mapped[int] = mapped_column(
        ForeignKey("offers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="stats")
    offer: Mapped["Offer"] = relationship()
