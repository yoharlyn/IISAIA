import { getDashboard } from "./api.js";

const SVG_NS = "http://www.w3.org/2000/svg";
const CHART_WIDTH = 780;
const CHART_HEIGHT = 292;
const PLOT = { top: 34, right: 16, bottom: 58, left: 46 };

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function svgElement(tag, className, text) {
  const node = document.createElementNS(SVG_NS, tag);
  if (className) node.setAttribute("class", className);
  if (text !== undefined) node.textContent = text;
  return node;
}

function headerCell(text, scope) {
  const cell = element("th", "", text);
  cell.setAttribute("scope", scope);
  return cell;
}

function tableRegion(table, label) {
  const region = element("div", "table-scroll");
  region.tabIndex = 0;
  region.setAttribute("role", "region");
  region.setAttribute("aria-label", label);
  region.append(table);
  return region;
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

export function integerScale(points) {
  const maximum = Math.max(0, ...points.map((point) => point.count));
  if (maximum === 0) return { axisMaximum: 1, ticks: [0] };
  const step = maximum <= 4 ? 1 : Math.ceil(maximum / 4);
  const axisMaximum = Math.max(1, Math.ceil(maximum / step) * step);
  const ticks = new Set();
  for (let value = 0; value <= axisMaximum; value += step) ticks.add(value);
  ticks.add(axisMaximum);
  return { axisMaximum, ticks: [...ticks].sort((left, right) => left - right) };
}

function shortMonth(point) {
  const [name, year] = point.label.split(" ");
  return `${name.slice(0, 3)} ${year.slice(-2)}`;
}

function chartSummary(points) {
  const total = points.reduce((sum, point) => sum + point.count, 0);
  if (total === 0) {
    return `No registraste visitas entre ${points[0].label} y ${points.at(-1).label}.`;
  }
  const maximum = Math.max(...points.map((point) => point.count));
  const peaks = points.filter((point) => point.count === maximum).map((point) => point.label);
  const activeMonths = points.filter((point) => point.count > 0).length;
  const visitWord = total === 1 ? "visita" : "visitas";
  const monthWord = activeMonths === 1 ? "mes" : "meses";
  return `${total} ${visitWord} en ${activeMonths} ${monthWord}. Máximo mensual: ${maximum} en ${peaks.join(" y ")}.`;
}

function chartSvg(points) {
  const svg = svgElement("svg", "visits-chart");
  svg.setAttribute("viewBox", `0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`);
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-labelledby", "visits-chart-svg-title visits-chart-svg-description");

  const title = svgElement("title", "", "Visitas mensuales de los últimos doce meses");
  title.id = "visits-chart-svg-title";
  const description = svgElement(
    "desc",
    "",
    "Gráfico de barras con escala entera desde cero. Cada barra incluye el mes y su cantidad; la tabla siguiente ofrece los mismos datos.",
  );
  description.id = "visits-chart-svg-description";
  svg.append(title, description);

  const plotWidth = CHART_WIDTH - PLOT.left - PLOT.right;
  const plotHeight = CHART_HEIGHT - PLOT.top - PLOT.bottom;
  const plotBottom = PLOT.top + plotHeight;
  const slotWidth = plotWidth / points.length;
  const barWidth = Math.min(38, slotWidth * 0.68);
  const { axisMaximum, ticks } = integerScale(points);

  ticks.forEach((tick) => {
    const y = plotBottom - (tick / axisMaximum) * plotHeight;
    const line = svgElement("line", "chart-grid-line");
    line.setAttribute("x1", String(PLOT.left));
    line.setAttribute("x2", String(CHART_WIDTH - PLOT.right));
    line.setAttribute("y1", String(y));
    line.setAttribute("y2", String(y));
    line.setAttribute("aria-hidden", "true");
    const label = svgElement("text", "chart-axis-label", String(tick));
    label.setAttribute("x", String(PLOT.left - 10));
    label.setAttribute("y", String(y + 4));
    label.setAttribute("text-anchor", "end");
    svg.append(line, label);
  });

  const axis = svgElement("line", "chart-axis-line");
  axis.setAttribute("x1", String(PLOT.left));
  axis.setAttribute("x2", String(CHART_WIDTH - PLOT.right));
  axis.setAttribute("y1", String(plotBottom));
  axis.setAttribute("y2", String(plotBottom));
  axis.setAttribute("aria-hidden", "true");
  svg.append(axis);

  points.forEach((point, index) => {
    const x = PLOT.left + index * slotWidth + (slotWidth - barWidth) / 2;
    const height = (point.count / axisMaximum) * plotHeight;
    const y = plotBottom - height;
    const bar = svgElement("rect", "chart-bar");
    bar.setAttribute("data-month", point.month);
    bar.setAttribute("data-count", String(point.count));
    bar.setAttribute("x", String(x));
    bar.setAttribute("y", String(y));
    bar.setAttribute("width", String(barWidth));
    bar.setAttribute("height", String(height));
    bar.setAttribute("rx", "4");
    const barTitle = svgElement("title", "", `${point.label}: ${point.count} visitas`);
    bar.append(barTitle);

    const month = svgElement("text", "chart-month-label", shortMonth(point));
    month.setAttribute("x", String(x + barWidth / 2));
    month.setAttribute("y", String(plotBottom + 25));
    month.setAttribute("text-anchor", "middle");
    svg.append(bar);
    if (point.count > 0) {
      const value = svgElement("text", "chart-value-label", String(point.count));
      value.setAttribute("x", String(x + barWidth / 2));
      value.setAttribute("y", String(Math.max(PLOT.top + 12, y - 8)));
      value.setAttribute("text-anchor", "middle");
      svg.append(value);
    }
    svg.append(month);
  });

  const axisTitle = svgElement("text", "chart-axis-title", "Visitas");
  axisTitle.setAttribute("x", String(PLOT.left));
  axisTitle.setAttribute("y", "18");
  svg.append(axisTitle);
  return svg;
}

function monthlyChart(points) {
  const figure = element("figure", "dashboard-figure");
  const heading = element("h3", "", "Visitas durante los últimos 12 meses");
  const summary = element("p", "chart-summary", chartSummary(points));
  summary.id = "visits-chart-summary";
  const scrollHint = element("p", "chart-scroll-hint", "Deslizá horizontalmente para recorrer los doce meses.");
  const chartRegion = element("div", "chart-scroll");
  chartRegion.tabIndex = 0;
  chartRegion.setAttribute("role", "region");
  chartRegion.setAttribute("aria-label", "Gráfico mensual. En pantallas estrechas, desplazá horizontalmente para recorrer los doce meses.");
  chartRegion.append(chartSvg(points));
  if (points.every((point) => point.count === 0)) {
    const empty = element("p", "chart-empty", "Sin visitas en este período. El gráfico conserva los doce meses y una escala de cero a uno.");
    figure.append(heading, summary, empty, scrollHint, chartRegion);
  } else {
    figure.append(heading, summary, scrollHint, chartRegion);
  }

  const table = element("table", "data-table");
  const caption = element("caption", "sr-only", "Visitas por mes y total acumulado");
  const head = document.createElement("thead");
  const headRow = document.createElement("tr");
  ["Mes", "Visitas", "Acumuladas"].forEach((label) => headRow.append(headerCell(label, "col")));
  head.append(headRow);
  const body = document.createElement("tbody");
  points.forEach((point) => {
    const row = document.createElement("tr");
    row.append(
      headerCell(point.label, "row"),
      element("td", "", point.count),
      element("td", "", point.cumulative),
    );
    body.append(row);
  });
  table.append(caption, head, body);
  figure.append(tableRegion(table, "Tabla equivalente del gráfico de visitas mensuales"));
  return figure;
}

function ratingTable(ratings) {
  const section = element("section", "dashboard-panel");
  section.append(element("h3", "", "Promedios personales"));
  const table = element("table", "data-table");
  table.append(element("caption", "sr-only", "Valoraciones personales por categoría"));
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
  section.append(tableRegion(table, "Promedios personales por categoría"));
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
  table.append(element("caption", "sr-only", "Cafeterías guardadas por barrio"));
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
      status.textContent = "";
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
