from pathlib import Path

import html5lib
import tinycss2

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def test_html_is_parseable_semantic_and_accessible() -> None:
    for filename in ("login.html", "catalog.html"):
        source = (FRONTEND / filename).read_text(encoding="utf-8")
        document = html5lib.HTMLParser(strict=True).parse(source)
        assert document is not None
        assert "<main" in source
        assert "aria-live" in source
        assert '<script type="module"' in source
        assert '<script type="module">' not in source
    login = (FRONTEND / "login.html").read_text(encoding="utf-8")
    assert 'for="username"' in login and 'for="password"' in login
    catalog = (FRONTEND / "catalog.html").read_text(encoding="utf-8")
    assert catalog.count('class="nav-link') == 1
    assert "Catálogo de productos" in catalog


def test_css_parses_and_local_assets_exist() -> None:
    css_path = FRONTEND / "assets/css/app.css"
    rules = tinycss2.parse_stylesheet(css_path.read_text(encoding="utf-8"), skip_whitespace=True)
    errors = [rule for rule in rules if rule.type == "error"]
    assert errors == []
    assert (FRONTEND / "assets/fonts/DMSans-Variable.woff2").stat().st_size > 10_000
    assert (FRONTEND / "assets/fonts/OFL.txt").exists()
    for module in ("api.js", "auth.js", "catalog.js", "login.js", "ui.js"):
        assert (FRONTEND / f"assets/js/{module}").exists()


def test_frontend_contains_no_seed_catalog() -> None:
    javascript = "\n".join(
        path.read_text(encoding="utf-8") for path in (FRONTEND / "assets/js").glob("*.js")
    )
    assert "IMP-CN-350-10" not in javascript
    assert "Implante cónico 3,5" not in javascript
