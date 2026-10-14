from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
import os
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageOps, UnidentifiedImageError

from backend.models import VisitPhoto


MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_VISIT_BYTES = 20 * 1024 * 1024
MAX_PIXELS = 20_000_000
MAX_PHOTOS_PER_VISIT = 5
FORMAT_RULES = {
    "JPEG": ("image/jpeg", ".jpg"),
    "PNG": ("image/png", ".png"),
    "WEBP": ("image/webp", ".webp"),
}


class UploadValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ProcessedImage:
    content: bytes
    mime_type: str
    extension: str
    width: int
    height: int
    sha256: str


def process_image(content: bytes, declared_mime: str | None) -> ProcessedImage:
    if not content:
        raise UploadValidationError("La fotografía está vacía.")
    if len(content) > MAX_FILE_BYTES:
        raise UploadValidationError("La fotografía supera el límite de 5 MiB.")
    if declared_mime not in {rule[0] for rule in FORMAT_RULES.values()}:
        raise UploadValidationError("El formato debe ser JPEG, PNG o WebP.")
    try:
        with Image.open(BytesIO(content)) as source:
            if getattr(source, "n_frames", 1) != 1:
                raise UploadValidationError("No se admiten imágenes animadas.")
            rule = FORMAT_RULES.get(source.format or "")
            if rule is None or rule[0] != declared_mime:
                raise UploadValidationError("El contenido no coincide con el MIME declarado.")
            width, height = source.size
            if width <= 0 or height <= 0 or width * height > MAX_PIXELS:
                raise UploadValidationError("La fotografía supera el límite de 20 megapíxeles.")
            source.load()
            normalized = ImageOps.exif_transpose(source)
            output = BytesIO()
            if source.format == "JPEG":
                normalized.convert("RGB").save(
                    output, format="JPEG", quality=88, optimize=True
                )
            elif source.format == "PNG":
                normalized.save(output, format="PNG", optimize=True)
            else:
                normalized.save(output, format="WEBP", quality=88, method=6)
    except UploadValidationError:
        raise
    except (Image.DecompressionBombError, UnidentifiedImageError, OSError, ValueError):
        raise UploadValidationError("El archivo no contiene una imagen válida.") from None
    encoded = output.getvalue()
    if len(encoded) > MAX_FILE_BYTES:
        raise UploadValidationError("La fotografía procesada supera el límite de 5 MiB.")
    return ProcessedImage(
        content=encoded,
        mime_type=rule[0],
        extension=rule[1],
        width=width,
        height=height,
        sha256=sha256(encoded).hexdigest(),
    )


def new_internal_name(extension: str) -> str:
    return f"{uuid4().hex}{extension}"


def photo_path(root: Path, photo: VisitPhoto) -> Path:
    if Path(photo.internal_name).name != photo.internal_name:
        raise ValueError("Nombre interno inválido.")
    directory = root / str(photo.owner_id) / str(photo.visit_id)
    candidate = directory / photo.internal_name
    if candidate.parent.resolve() != directory.resolve():
        raise ValueError("Ruta interna inválida.")
    return candidate


def write_photo(root: Path, photo: VisitPhoto, content: bytes) -> Path:
    destination = photo_path(root, photo)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.parent / f".{uuid4().hex}.tmp"
    try:
        with temporary.open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()
    return destination


def quarantine_photos(root: Path, photos: list[VisitPhoto]) -> list[tuple[Path, Path]]:
    moved: list[tuple[Path, Path]] = []
    quarantine = root / ".quarantine"
    for photo in photos:
        source = photo_path(root, photo)
        if not source.exists():
            continue
        quarantine.mkdir(parents=True, exist_ok=True)
        target = quarantine / f"{uuid4().hex}-{photo.internal_name}"
        os.replace(source, target)
        moved.append((source, target))
    return moved


def restore_quarantined(moved: list[tuple[Path, Path]]) -> None:
    for original, quarantined in reversed(moved):
        if not quarantined.exists():
            continue
        original.parent.mkdir(parents=True, exist_ok=True)
        os.replace(quarantined, original)


def purge_quarantined(moved: list[tuple[Path, Path]]) -> None:
    for _, quarantined in moved:
        if quarantined.exists():
            quarantined.unlink()
