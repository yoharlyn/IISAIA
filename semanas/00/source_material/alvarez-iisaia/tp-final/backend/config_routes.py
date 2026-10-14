from fastapi import APIRouter, Depends, Request

from backend.auth_routes import AuthContext, require_auth


router = APIRouter(prefix="/api")


@router.get("/config")
def public_config(
    request: Request, _context: AuthContext = Depends(require_auth)
) -> dict[str, str | bool | None]:
    settings = request.app.state.settings
    enabled = bool(settings.google_maps_browser_key and settings.google_map_id)
    return {
        "google_maps_enabled": enabled,
        "google_maps_browser_key": settings.google_maps_browser_key if enabled else None,
        "google_map_id": settings.google_map_id if enabled else None,
    }
