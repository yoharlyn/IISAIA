from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select

from backend.db import SessionLocal
from backend.models import Category, ImplantSpecs, Product, User, UserRole
from backend.services.auth import hash_password

CATEGORIES = ("Implantes", "Instrumental", "Regeneración")

PRODUCTS = (
    {
        "sku": "IMP-CN-350-10",
        "name": "Implante cónico 3,5 × 10 mm",
        "description": "Implante de titanio grado 4 para carga diferida.",
        "brand": "NovaDent",
        "category": "Implantes",
        "manufacturer_name": "BioImplant Argentina",
        "price_cents": 128500,
        "stock": 24,
        "specs": ("3.50", "10.00", "Cono Morse", "Titanio grado 4", "SLA"),
    },
    {
        "sku": "IMP-CN-400-115",
        "name": "Implante cónico 4,0 × 11,5 mm",
        "description": "Implante de titanio con conexión interna.",
        "brand": "NovaDent",
        "category": "Implantes",
        "manufacturer_name": "BioImplant Argentina",
        "price_cents": 134900,
        "stock": 18,
        "specs": ("4.00", "11.50", "Cono Morse", "Titanio grado 4", "SLA"),
    },
    {
        "sku": "IMP-HX-450-13",
        "name": "Implante hexágono interno 4,5 × 13 mm",
        "description": "Diseño autorroscante para hueso de densidad media.",
        "brand": "OralTech",
        "category": "Implantes",
        "manufacturer_name": "OralTech Medical",
        "price_cents": 142000,
        "stock": 12,
        "specs": ("4.50", "13.00", "Hexágono interno", "Ti-6Al-4V", "RBM"),
    },
    {
        "sku": "IMP-ZR-400-10",
        "name": "Implante cerámico 4,0 × 10 mm",
        "description": "Implante monocomponente libre de metal.",
        "brand": "CeramFix",
        "category": "Implantes",
        "manufacturer_name": "CeramFix Dental",
        "price_cents": 219000,
        "stock": 8,
        "specs": ("4.00", "10.00", "Monocomponente", "Zirconia", "Arenado"),
    },
    {
        "sku": "INS-KIT-001",
        "name": "Kit quirúrgico universal",
        "description": "Instrumental autoclavable para cirugía implantológica.",
        "brand": "NovaDent",
        "category": "Instrumental",
        "manufacturer_name": "BioImplant Argentina",
        "price_cents": 785000,
        "stock": 4,
    },
    {
        "sku": "INS-TORQ-035",
        "name": "Torquímetro protésico",
        "description": "Rango de ajuste de 10 a 35 Ncm.",
        "brand": "OralTech",
        "category": "Instrumental",
        "manufacturer_name": "OralTech Medical",
        "price_cents": 189500,
        "stock": 9,
    },
    {
        "sku": "INS-DRL-200",
        "name": "Fresa piloto 2,0 mm",
        "description": "Fresa de acero quirúrgico con marcas de profundidad.",
        "brand": "OralTech",
        "category": "Instrumental",
        "manufacturer_name": "OralTech Medical",
        "price_cents": 45900,
        "stock": 35,
    },
    {
        "sku": "REG-MEM-2030",
        "name": "Membrana de colágeno 20 × 30 mm",
        "description": "Membrana reabsorbible para regeneración ósea guiada.",
        "brand": "RegenPlus",
        "category": "Regeneración",
        "manufacturer_name": "Biomaterials Sur",
        "price_cents": 96500,
        "stock": 16,
    },
    {
        "sku": "REG-XEN-050",
        "name": "Sustituto óseo granulado 0,5 g",
        "description": "Xenoinjerto mineral de granulometría fina.",
        "brand": "RegenPlus",
        "category": "Regeneración",
        "manufacturer_name": "Biomaterials Sur",
        "price_cents": 112000,
        "stock": 21,
    },
    {
        "sku": "REG-PLUG-10",
        "name": "Esponja hemostática de colágeno",
        "description": "Caja de diez unidades estériles.",
        "brand": "RegenPlus",
        "category": "Regeneración",
        "manufacturer_name": "Biomaterials Sur",
        "price_cents": 67800,
        "stock": 30,
    },
)


def run_seed(password: str, username: str = "dentista.demo") -> None:
    if len(password) < 8:
        raise ValueError("SEED_DENTIST_PASSWORD must contain at least 8 characters")
    now = datetime.now(UTC)
    with SessionLocal() as db, db.begin():
        user = db.scalar(select(User).where(User.username == username.lower()))
        if user is None:
            db.add(
                User(
                    username=username.lower(),
                    email="dentista.demo@example.test",
                    password_hash=hash_password(password),
                    first_name="Marina",
                    last_name="Álvarez",
                    role=UserRole.DENTIST,
                    is_active=True,
                    created_at=now,
                    updated_at=now,
                )
            )
        else:
            user.password_hash = hash_password(password)
            user.is_active = True
            user.role = UserRole.DENTIST
            user.updated_at = now

        categories: dict[str, Category] = {}
        for name in CATEGORIES:
            category = db.scalar(select(Category).where(Category.name == name))
            if category is None:
                category = Category(name=name, is_active=True)
                db.add(category)
                db.flush()
            categories[name] = category

        for item in PRODUCTS:
            product = db.scalar(select(Product).where(Product.sku == item["sku"]))
            fields = {
                "name": item["name"],
                "description": item["description"],
                "brand": item["brand"],
                "category_id": categories[item["category"]].id,
                "manufacturer_name": item["manufacturer_name"],
                "price_cents": item["price_cents"],
                "stock": item["stock"],
                "is_active": True,
                "is_implant": "specs" in item,
                "updated_at": now,
            }
            if product is None:
                product = Product(sku=item["sku"], created_at=now, **fields)
                db.add(product)
                db.flush()
            else:
                for field_name, value in fields.items():
                    setattr(product, field_name, value)
            specs = item.get("specs")
            if specs:
                spec_fields = {
                    "diameter_mm": Decimal(specs[0]),
                    "length_mm": Decimal(specs[1]),
                    "connection_type": specs[2],
                    "material": specs[3],
                    "surface_treatment": specs[4],
                }
                if product.implant_specs is None:
                    product.implant_specs = ImplantSpecs(**spec_fields)
                else:
                    for field_name, value in spec_fields.items():
                        setattr(product.implant_specs, field_name, value)
            elif product.implant_specs is not None:
                db.delete(product.implant_specs)


def main() -> None:
    password = os.getenv("SEED_DENTIST_PASSWORD")
    if not password:
        raise SystemExit("SEED_DENTIST_PASSWORD is required")
    run_seed(password, os.getenv("SEED_DENTIST_USERNAME", "dentista.demo"))
    print("Seed completed successfully.")


if __name__ == "__main__":
    main()
