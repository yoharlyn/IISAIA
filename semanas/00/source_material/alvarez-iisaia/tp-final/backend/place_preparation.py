from sqlmodel import Session, select

from backend.google_places import PlacesProvider
from backend.locations import fetch_verified_location
from backend.models import Cafe
from backend.schemas import PreparedCafeRead


async def prepare_cafe(
    provider: PlacesProvider,
    session: Session,
    *,
    owner_id: int,
    place_id: str,
) -> PreparedCafeRead:
    """Valida un lugar sin persistirlo y busca duplicados del propietario."""
    verified = await fetch_verified_location(provider, place_id=place_id)
    existing = session.exec(
        select(Cafe).where(
            Cafe.owner_id == owner_id,
            Cafe.place_id == verified.details.place_id,
        )
    ).first()
    return PreparedCafeRead(
        place_id=verified.details.place_id,
        display_name=verified.details.display_name,
        formatted_address=verified.details.formatted_address,
        neighborhood=verified.neighborhood,
        already_saved=existing is not None,
        existing_cafe_id=existing.id if existing is not None else None,
    )
