from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
DASHBOARD = (ROOT / "frontend" / "js" / "dashboard.js").read_text(encoding="utf-8")
RECOMMENDATIONS = (ROOT / "frontend" / "js" / "recommendations.js").read_text(
    encoding="utf-8"
)
STYLES = (ROOT / "frontend" / "css" / "styles.css").read_text(encoding="utf-8")


def test_sections_and_navigation_follow_the_v36_order():
    menu = [
        'href="#descubrir">Descubrir',
        'href="#coleccion">Mis cafeterías',
        'href="#mapa">Mapa',
        'href="#dashboard">Dashboard',
    ]
    sections = ['id="descubrir"', 'id="coleccion"', 'id="mapa"', 'id="dashboard"']

    assert [INDEX.index(item) for item in menu] == sorted(INDEX.index(item) for item in menu)
    assert [INDEX.index(item) for item in sections] == sorted(
        INDEX.index(item) for item in sections
    )
    assert 'href="#explorar"' not in INDEX
    assert 'id="explorar"' not in INDEX
    assert INDEX.index('id="coleccion"') < INDEX.index('id="filter-form"')
    assert INDEX.index('id="filter-form"') < INDEX.index('id="cafe-grid"')
    assert INDEX.count('id="filter-form"') == 1
    assert INDEX.count('tabindex="-1"') >= 5
    assert 'href="#main-content">Saltar al contenido' in INDEX


def test_chart_has_unique_integer_ticks_and_labels_only_positive_values():
    assert "const ticks = new Set()" in DASHBOARD
    assert "ticks: [...ticks].sort((left, right) => left - right)" in DASHBOARD
    assert "if (maximum === 0) return { axisMaximum: 1, ticks: [0] }" in DASHBOARD
    assert "if (point.count > 0)" in DASHBOARD
    assert 'element("td", "", point.count)' in DASHBOARD
    assert 'element("td", "", point.cumulative)' in DASHBOARD
    assert 'className = "chart-scroll-hint"' not in DASHBOARD
    assert '"chart-scroll-hint"' in DASHBOARD
    assert ".chart-scroll { overflow-x: visible" in STYLES
    assert ".visits-chart { width: 660px; min-width: 660px; }" in STYLES


def test_recommendations_are_paginated_locally_in_groups_of_four():
    assert "export const RECOMMENDATIONS_PER_PAGE = 4" in RECOMMENDATIONS
    assert "items.slice(start, start + RECOMMENDATIONS_PER_PAGE)" in RECOMMENDATIONS
    assert '"Anterior"' in RECOMMENDATIONS
    assert '"Siguiente"' in RECOMMENDATIONS
    assert "Página ${currentPage} de ${page.pageCount}" in RECOMMENDATIONS
    assert 'indicator.setAttribute("aria-current", "page")' in RECOMMENDATIONS
    assert 'announcement.setAttribute("aria-live", "polite")' in RECOMMENDATIONS
    assert "pagination.hidden = page.pageCount <= 1" in RECOMMENDATIONS
    assert "focus({ preventScroll: true })" in RECOMMENDATIONS
    assert "let currentPage = 1" in RECOMMENDATIONS
    assert "fetch(" not in RECOMMENDATIONS
    assert "searchRecommendations" not in RECOMMENDATIONS


def test_requested_visible_copy_is_absent():
    combined = INDEX + DASHBOARD
    removed = [
        "Dashboard actualizado.",
        "Las barras muestran visitas registradas por mes; la escala y las líneas horizontales representan cantidades enteras desde cero.",
        "Cada barra representa visitas registradas en un mes; el valor también aparece escrito sobre la barra.",
        "Detalle mensual de visitas",
        "Promedio y cantidad de valoraciones por categoría",
        "Cantidad de cafeterías guardadas por barrio",
        "Incluye los 48 barrios oficiales y, si existen, tus valores históricos.",
        "También podés seleccionar un punto de interés del mapa si Google informa un Place ID. La ubicación actual permanece sólo en memoria. Distancias en línea recta, no tiempos de viaje.",
        "Cada resultado separa los datos actuales de Google Maps, el cálculo determinístico realizado para tu atlas y la información que se guardaría localmente.",
    ]

    assert all(text not in combined for text in removed)
