from sqlmodel import Session, func, select

from backend.models import Cafe, VisitStatus

SEED_CAFES = (
    {
        "name": "Bruma Café",
        "neighborhood": "Palermo",
        "description": "Filtrados precisos y una barra luminosa para probar granos de estación.",
        "image_url": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=1200&q=80",
        "visit_status": VisitStatus.VISITED,
        "is_favorite": True,
        "coffee_rating": 5,
        "food_rating": 4,
        "ambience_rating": 5,
        "service_rating": 5,
    },
    {
        "name": "Oliva Tostadores",
        "neighborhood": "Villa Crespo",
        "description": "Tostado propio, mesas compartidas y una carta breve de pastelería.",
        "image_url": "https://images.unsplash.com/photo-1445116572660-236099ec97a0?auto=format&fit=crop&w=1200&q=80",
        "visit_status": VisitStatus.VISITED,
        "coffee_rating": 4,
        "food_rating": 3,
        "ambience_rating": 5,
        "service_rating": 4,
    },
    {
        "name": "Patio Terracota",
        "neighborhood": "San Telmo",
        "description": "Un patio tranquilo que queda pendiente para una mañana de fin de semana.",
        "image_url": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=1200&q=80",
        "visit_status": VisitStatus.PENDING,
        "is_favorite": True,
    },
    {
        "name": "Andén Café",
        "neighborhood": "Chacarita",
        "description": "Una barra compacta cerca de la estación con opciones para llevar.",
        "visit_status": VisitStatus.PENDING,
    },
    {
        "name": "Nido Espresso",
        "neighborhood": "Colegiales",
        "description": "Espresso balanceado y atención cercana en un salón pequeño.",
        "image_url": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?auto=format&fit=crop&w=1200&q=80",
        "visit_status": VisitStatus.VISITED,
        "is_favorite": True,
        "coffee_rating": 5,
        "food_rating": 4,
        "ambience_rating": 4,
        "service_rating": 5,
    },
    {
        "name": "Umbral Café",
        "neighborhood": "Almagro",
        "description": "Café de barrio renovado, con buena cocina y mesas amplias.",
        "visit_status": VisitStatus.VISITED,
        "coffee_rating": 3,
        "food_rating": 4,
        "ambience_rating": 4,
        "service_rating": 5,
    },
    {
        "name": "Surco Café",
        "neighborhood": "Belgrano",
        "description": "Una cafetería serena con granos latinoamericanos por descubrir.",
        "visit_status": VisitStatus.PENDING,
    },
)


def seed_cafes(engine) -> None:
    with Session(engine) as session:
        if session.exec(select(func.count()).select_from(Cafe)).one() > 0:
            return
        session.add_all(Cafe(**data) for data in SEED_CAFES)
        session.commit()

