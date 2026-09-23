"""Create the Version 1 schema."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_v1_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "role IN ('ADMIN','DENTIST','DISTRIBUTOR','MANUFACTURER')",
            name="ck_users_role_values",
        ),
        sa.UniqueConstraint("username", name="uq_users_username"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_role_active", "users", ["role", "is_active"])

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("name", name="uq_categories_name"),
    )
    op.create_index("ix_categories_active", "categories", ["is_active"])

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sku", sa.String(64), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("brand", sa.String(100), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("manufacturer_name", sa.String(200), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_implant", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("price_cents >= 0", name="ck_products_price_nonnegative"),
        sa.CheckConstraint("stock >= 0", name="ck_products_stock_nonnegative"),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name="fk_products_category_id_categories",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("sku", name="uq_products_sku"),
    )
    op.create_index("ix_products_category_id", "products", ["category_id"])
    op.create_index("ix_products_active_name", "products", ["is_active", "name"])
    op.create_index("ix_products_active_category", "products", ["is_active", "category_id"])
    op.create_index("ix_products_active_implant", "products", ["is_active", "is_implant"])

    op.create_table(
        "implant_specs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("diameter_mm", sa.Numeric(5, 2), nullable=False),
        sa.Column("length_mm", sa.Numeric(5, 2), nullable=False),
        sa.Column("connection_type", sa.String(100), nullable=True),
        sa.Column("material", sa.String(100), nullable=True),
        sa.Column("surface_treatment", sa.String(150), nullable=True),
        sa.CheckConstraint("diameter_mm > 0", name="ck_implant_specs_diameter_positive"),
        sa.CheckConstraint("length_mm > 0", name="ck_implant_specs_length_positive"),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_implant_specs_product_id_products",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("product_id", name="uq_implant_specs_product_id"),
    )


def downgrade() -> None:
    op.drop_table("implant_specs")
    op.drop_index("ix_products_active_implant", table_name="products")
    op.drop_index("ix_products_active_category", table_name="products")
    op.drop_index("ix_products_active_name", table_name="products")
    op.drop_index("ix_products_category_id", table_name="products")
    op.drop_table("products")
    op.drop_index("ix_categories_active", table_name="categories")
    op.drop_table("categories")
    op.drop_index("ix_users_role_active", table_name="users")
    op.drop_table("users")
