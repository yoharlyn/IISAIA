from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

pytestmark = pytest.mark.e2e


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for_server(url: str, process: subprocess.Popen, timeout: float = 15) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise RuntimeError(f"Server exited early:\n{stdout}\n{stderr}")
        try:
            with urllib.request.urlopen(url, timeout=0.5) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.1)
    raise TimeoutError(f"Server did not become ready at {url}")


def test_complete_dentist_browser_flow(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    database = tmp_path / "e2e.db"
    port = free_port()
    base_url = f"http://127.0.0.1:{port}"
    env = os.environ | {
        "APP_ENV": "test",
        "DATABASE_URL": f"sqlite:///{database}",
        "SESSION_SECRET": "e2e-session-secret-at-least-32-characters",
        "SESSION_COOKIE_SECURE": "false",
        "ALLOWED_ORIGINS": base_url,
        "TRUSTED_ORIGINS": base_url,
        "SEED_DENTIST_USERNAME": "dentista.demo",
        "SEED_DENTIST_PASSWORD": "DemoLocal123!",
    }
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=root,
        env=env,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [sys.executable, "-m", "backend.scripts.seed"],
        cwd=root,
        env=env,
        check=True,
        capture_output=True,
    )
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        wait_for_server(f"{base_url}/login", server)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            browser_errors: list[str] = []
            page.on(
                "console",
                lambda message: (
                    browser_errors.append(message.text) if message.type == "error" else None
                ),
            )
            page.on("pageerror", lambda error: browser_errors.append(str(error)))

            page.goto(f"{base_url}/login")
            page.get_by_label("Nombre de usuario").fill("dentista.demo")
            page.get_by_label("Contraseña").fill("DemoLocal123!")
            page.get_by_role("button", name="Ingresar").click()
            page.wait_for_url(f"{base_url}/catalogo")
            page.get_by_role("heading", name="Catálogo de productos").wait_for()
            assert page.locator(".nav-link").all_inner_texts() == ["Catálogo de productos"]
            page.locator(".product-card").first.wait_for()
            assert page.locator(".product-card").count() == 6
            assert page.get_by_text("Implante", exact=True).first.is_visible()

            page.get_by_role("button", name="Siguiente").click()
            page.get_by_text("Página 2 de 2").wait_for()
            assert page.locator(".product-card").count() == 4
            page.set_viewport_size({"width": 320, "height": 720})
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")

            page.get_by_label("Buscar").fill("OralTech")
            page.get_by_role("button", name="Aplicar filtros").click()
            page.get_by_text("productos encontrados").wait_for()
            assert page.locator(".product-card").count() >= 1
            assert "OralTech" in page.locator(".product-grid").inner_text()

            page.get_by_label("Buscar").fill("")
            page.get_by_label("Tipo").select_option("true")
            page.get_by_role("button", name="Aplicar filtros").click()
            page.locator(".product-card").first.wait_for()
            assert page.locator(".implant-tag").count() == page.locator(".product-card").count()

            page.get_by_role("button", name="Cerrar sesión").click()
            page.wait_for_url(f"{base_url}/login")
            page.goto(f"{base_url}/catalogo")
            page.wait_for_url(f"{base_url}/login")
            unexpected_errors = [
                message for message in browser_errors if "401 (Unauthorized)" not in message
            ]
            assert unexpected_errors == []
            browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)
