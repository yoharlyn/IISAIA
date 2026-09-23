from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    false,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (Index("ix_categories_active", "is_active"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )


class Product(TimestampMixin, Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("price_cents >= 0", name="price_nonnegative"),
        CheckConstraint("stock >= 0", name="stock_nonnegative"),
        Index("ix_products_active_name", "is_active", "name"),
        Index("ix_products_active_category", "is_active", "category_id"),
        Index("ix_products_active_implant", "is_active", "is_implant"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    brand: Mapped[str | None] = mapped_column(String(100))
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), index=True
    )
    manufacturer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    price_cents: Mapped[int] = mapped_column(nullable=False)
    stock: Mapped[int] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    is_implant: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )

    category: Mapped[Category] = relationship(lazy="joined")
    implant_specs: Mapped["ImplantSpecs | None"] = relationship(
        back_populates="product", uselist=False, cascade="all, delete-orphan", lazy="joined"
    )


class ImplantSpecs(Base):
    __tablename__ = "implant_specs"
    __table_args__ = (
        CheckConstraint("diameter_mm > 0", name="diameter_positive"),
        CheckConstraint("length_mm > 0", name="length_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    diameter_mm: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    length_mm: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    connection_type: Mapped[str | None] = mapped_column(String(100))
    material: Mapped[str | None] = mapped_column(String(100))
    surface_treatment: Mapped[str | None] = mapped_column(String(150))

    product: Mapped[Product] = relationship(back_populates="implant_specs")
