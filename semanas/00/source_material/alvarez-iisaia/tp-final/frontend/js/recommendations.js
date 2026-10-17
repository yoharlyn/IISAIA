function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

const FACTOR_LABELS = {
  proximity: "Cercanía",
  google_rating: "Rating de Google Maps",
  review_confidence: "Cantidad de reseñas",
  novelty: "Novedad en tu atlas",
  personal_affinity: "Afinidad personal por barrio",
};

const BUSINESS_LABELS = {
  OPERATIONAL: "Abierta según Google Maps",
  CLOSED_TEMPORARILY: "Cerrada temporalmente según Google Maps",
};

function heading(text) {
  return element("h4", "recommendation-group-title", text);
}

function detailsList(rows) {
  const list = element("dl", "recommendation-details");
  rows.forEach(([label, value]) => {
    const row = element("div", "recommendation-detail-row");
    row.append(element("dt", "", label), element("dd", "", value));
    list.append(row);
  });
  return list;
}

function futureOpening(value) {
  if (!value) return null;
  const opening = new Date(`${value}T00:00:00`);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return opening > today ? value : null;
}

function googleMapsLink(value) {
  if (!value) return null;
  try {
    const url = new URL(value);
    const isGoogleHost = url.hostname === "google.com" || url.hostname.endsWith(".google.com");
    if (url.protocol !== "https:" || !isGoogleHost) return null;
    const link = element("a", "google-maps-link", "Ver ficha actual en Google Maps");
    link.href = url.toString();
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    return link;
  } catch {
    return null;
  }
}

function googleData(item) {
  const section = element("section", "recommendation-group recommendation-google");
  const rating = item.rating === null
    ? "No informado"
    : `${item.rating.toFixed(1)} de 5`;
  const reviews = item.user_rating_count === null
    ? "No informada"
    : new Intl.NumberFormat("es-AR").format(item.user_rating_count);
  section.append(
    heading("Datos actuales de Google Maps"),
    detailsList([
      ["Dirección", item.formatted_address || "No informada"],
      ["Rating", rating],
      ["Cantidad de reseñas", reviews],
      ["Estado comercial", BUSINESS_LABELS[item.business_status] || "No informado"],
    ]),
  );
  const opening = futureOpening(item.opening_date);
  if (opening) section.append(element("p", "opening-note", `Próxima apertura informada: ${opening}`));
  const link = googleMapsLink(item.google_maps_uri);
  if (link) section.append(link);
  section.append(element("p", "google-attribution", `Fuente y atribución: ${item.attribution}`));
  return section;
}

function personalCalculation(item) {
  const section = element("section", "recommendation-group recommendation-personal");
  const factors = element("ul", "factor-list");
  Object.entries(item.factors).forEach(([key, contribution]) => {
    const label = FACTOR_LABELS[key] || key;
    factors.append(element("li", "", `${label}: ${(contribution * 100).toFixed(0)} puntos`));
  });
  section.append(
    heading("Cálculo para tu atlas"),
    detailsList([
      ["Distancia", `${item.distance_km.toFixed(1)} km en línea recta`],
      ["Estado en tu atlas", item.novelty_label],
      ["Puntaje determinístico", `${(item.score * 100).toFixed(0)} de 100`],
    ]),
    element("p", "factor-intro", "Contribución de los factores disponibles:"),
    factors,
  );
  return section;
}

function recommendationCard(item) {
  const card = element("article", "recommendation-card");
  card.append(
    element("h3", "", item.display_name || "Nombre no informado"),
    googleData(item),
    personalCalculation(item),
  );
  const saveGroup = element("section", "recommendation-group recommendation-save");
  saveGroup.append(
    heading("Antes de guardar"),
    element("p", "", "Verificaremos nuevamente el nombre, la dirección y el barrio antes de abrir el formulario. Sólo se guardará cuando confirmes la acción."),
  );
  const button = element("button", "button button-primary", "Agregar a mis cafeterías");
  button.type = "button";
  button.addEventListener("click", () => document.dispatchEvent(
    new CustomEvent("coffee-atlas:prepare-recommendation", { detail: { item, trigger: button } }),
  ));
  saveGroup.append(button);
  card.append(saveGroup);
  return card;
}

export function renderRecommendations(container, items) {
  container.replaceChildren(...items.map(recommendationCard));
  if (!items.length) {
    container.append(element("p", "empty-state", "No encontramos recomendaciones para ese radio."));
  }
}

export function renderRecommendationsUnavailable(container, message) {
  container.replaceChildren(
    element("p", "empty-state recommendation-unavailable", message),
  );
}
