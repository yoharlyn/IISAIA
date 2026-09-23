from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.api.auth import router as auth_router
from backend.api.products import router as products_router
from backend.config import PROJECT_ROOT, get_settings
from backend.errors import install_error_handlers
from backend.logging import request_context_middleware

settings = get_settings()
logging.basicConfig(
    level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)

app = FastAPI(
    title="Catálogo odontológico API",
    version="1.0.0",
    openapi_version="3.1.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-CSRF-Protection", "X-Request-ID"],
)
app.middleware("http")(request_context_middleware)
install_error_handlers(app)
app.include_router(auth_router)
app.include_router(products_router)

frontend = PROJECT_ROOT / "frontend"
assets = frontend / "assets"
if assets.exists():
    app.mount("/assets", StaticFiles(directory=assets), name="assets")


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse("/login", status_code=302)


@app.get("/login", include_in_schema=False)
def login_page() -> FileResponse:
    return FileResponse(frontend / "login.html")


@app.get("/catalogo", include_in_schema=False)
def catalog_page() -> FileResponse:
    return FileResponse(frontend / "catalog.html")
