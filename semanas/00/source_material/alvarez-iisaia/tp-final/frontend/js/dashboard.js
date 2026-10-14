import { getDashboard } from "./api.js";

const SVG_NS = "http://www.w3.org/2000/svg";

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function summaryCards(summary) {
  const labels = [
    ["total_visits", "Visitas registradas"],
    ["visited_cafes", "Cafeterías visitadas"],
    ["pending_cafes", "Cafeterías pendientes"],
    ["favorite_cafes", "Favoritas"],
  ];
  return labels.map(([key, label]) => {
    const card = element("article", "dashboard-summary-card");
    card.append(element("strong", "", summary[key]), element("span", "", label));
    return card;
  });
}

function monthlyChart(points) {
  const figure = element("figure", "dashboard-figure");
  const heading = element("h3", "", "Visitas durante los últimos 12 meses");
  const description = element("p", "chart-description", "Las barras muestran visitas por mes. La tabla presenta los mismos valores y la evolución acumulada.");
  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("viewBox", "0 0 720 260");
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", "Gráfico de visitas mensuales; los valores completos están en la tabla siguiente.");
  const maximum = Math.max(1, ...points.map((point) => point.count));
  points.forEach((point, index) => {
    const height = (point.count / maximum) * 190;
    const bar = document.createElementNS(SVG_NS, "rect");
    bar.setAttribute("x", String(22 + index * 58));
    bar.setAttribute("y", String(215 - height));
    bar.setAttribute("width", "36");
    bar.setAttribute("height", String(height));
    bar.setAttribute("rx", "5");
    const title = document.createElementNS(SVG_NS, "title");
    title.textContent = `${point.label}: ${point.count} visitas`;
    bar.append(title);
    svg.append(bar);
  });
  const table = element("table", "data-table");
  const caption = element("caption", "", "Detalle mensual de visitas");
  const head = document.createElement("thead");
  const headRow = document.createElement("tr");
  ["Mes", "Visitas", "Acumuladas"].forEach((label) => headRow.append(element("th", "", label)));
  head.append(headRow);
  const body = document.createElement("tbody");
  points.forEach((point) => {
    const row = document.createElement("tr");
    row.append(
      element("th", "", point.label),
      element("td", "", point.count),
      element("td", "", point.cumulative),
    );
    body.append(row);
  });
  table.append(caption, head, body);
  figure.append(heading, description, svg, table);
  return figure;
}

function ratingTable(ratings) {
  const section = element("section", "dashboard-panel");
  section.append(element("h3", "", "Promedios personales"));
  const table = element("table", "data-table");
  table.append(element("caption", "", "Promedio y cantidad de valoraciones por categoría"));
  const head = document.createElement("thead");
  const headRow = document.createElement("tr");
  ["Categoría", "Promedio", "Valoraciones"].forEach((label) => headRow.append(element("th", "", label)));
  head.append(headRow);
  const body = document.createElement("tbody");
  ratings.forEach((rating) => {
    const row = document.createElement("tr");
    const average = rating.average === null ? "Sin datos" : `${rating.average.toFixed(2)} de 5`;
    row.append(element("th", "", rating.label), element("td", "", average), element("td", "", rating.count));
    body.append(row);
  });
  table.append(head, body);
  section.append(table);
  return section;
}

function neighborhoodTable(neighborhoods) {
  const section = element("section", "dashboard-panel");
  section.append(element("h3", "", "Distribución por barrio"));
  if (!neighborhoods.length) {
    section.append(element("p", "empty-copy", "Todavía no hay cafeterías para distribuir."));
    return section;
  }
  const table = element("table", "data-table");
  table.append(element("caption", "", "Cantidad de cafeterías guardadas por barrio"));
  const body = document.createElement("tbody");
  neighborhoods.forEach((item) => {
    const row = document.createElement("tr");
    row.append(element("th", "", item.neighborhood), element("td", "", item.count));
    body.append(row);
  });
  table.append(body);
  section.append(table);
  return section;
}

function rankedList(title, items, formatter, emptyMessage) {
  const section = element("section", "dashboard-panel");
  section.append(element("h3", "", title));
  if (!items.length) {
    section.append(element("p", "empty-copy", emptyMessage));
    return section;
  }
  const list = document.createElement("ol");
  list.className = "dashboard-ranking";
  items.forEach((item) => list.append(element("li", "", formatter(item))));
  section.append(list);
  return section;
}

export function renderDashboard(container, dashboard) {
  const summary = element("div", "dashboard-summary");
  summary.replaceChildren(...summaryCards(dashboard.summary));
  const details = element("div", "dashboard-details");
  details.append(
    ratingTable(dashboard.rating_averages),
    neighborhoodTable(dashboard.neighborhoods),
    rankedList(
      "Cafeterías mejor puntuadas",
      dashboard.top_cafes,
      (item) => `${item.name}: ${item.average_rating.toFixed(2)} de 5, ${item.visit_count} visitas`,
      "Todavía no hay valoraciones para comparar.",
    ),
    rankedList(
      "Pendientes más cercanas",
      dashboard.nearby_pending,
      (item) => `${item.name}, ${item.neighborhood}: ${item.distance_km.toFixed(2)} km en línea recta`,
      "Configurá un domicilio vigente y ubicaciones verificadas para calcular cercanía.",
    ),
  );
  container.replaceChildren(summary, monthlyChart(dashboard.monthly_visits), details);
}

export function initializeDashboard() {
  const container = document.querySelector("#dashboard-content");
  const status = document.querySelector("#dashboard-status");

  async function load() {
    status.textContent = "Cargando dashboard…";
    container.setAttribute("aria-busy", "true");
    try {
      const dashboard = await getDashboard();
      renderDashboard(container, dashboard);
      status.textContent = "Dashboard actualizado.";
    } catch (error) {
      container.replaceChildren();
      status.textContent = error.message;
      status.classList.add("error");
    } finally {
      container.setAttribute("aria-busy", "false");
    }
  }

  return { load };
}
