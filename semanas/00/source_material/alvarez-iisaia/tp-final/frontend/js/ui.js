const RATING_LABELS = [
  ["coffee_rating", "Café"],
  ["food_rating", "Comida"],
  ["ambience_rating", "Ambiente"],
  ["service_rating", "Atención"],
];

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

const ICON_PATHS = {
  heart: ["M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1 1L12 21l7.8-7.6a5.5 5.5 0 0 0 1-8.8Z"],
  visits: ["M8 2v4M16 2v4M3 9h18", "M5 4h14a2 2 0 0 1 2 2v14H3V6a2 2 0 0 1 2-2Z"],
  edit: ["M12 20h9", "M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4Z"],
  delete: ["M3 6h18M8 6V4h8v2M19 6l-1 15H6L5 6", "M10 11v6M14 11v6"],
};

function icon(name) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("aria-hidden", "true");
  ICON_PATHS[name].forEach((data) => {
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", data);
    svg.append(path);
  });
  return svg;
}

function imageFallback(name) {
  const fallback = element("div", "image-fallback");
  fallback.setAttribute("role", "img");
  fallback.setAttribute("aria-label", `${name}, sin fotografía`);
  fallback.append(element("span", "fallback-mark", "CA"), element("span", "", "Sin fotografía"));
  return fallback;
}

function cardMedia(cafe) {
  const media = element("div", "card-media");
  const fallback = imageFallback(cafe.name);
  if (cafe.image_url) {
    const image = document.createElement("img");
    image.src = cafe.image_url;
    image.alt = `Fotografía de ${cafe.name}`;
    image.loading = "lazy";
    image.referrerPolicy = "no-referrer";
    fallback.hidden = true;
    image.addEventListener("error", () => {
      image.hidden = true;
      fallback.hidden = false;
    }, { once: true });
    media.append(image);
  }
  media.append(fallback);

  const favorite = element("button", "favorite-button");
  favorite.type = "button";
  favorite.dataset.action = "toggle-favorite";
  favorite.dataset.id = cafe.id;
  favorite.setAttribute("aria-pressed", String(cafe.is_favorite));
  favorite.append(
    icon("heart"),
    document.createTextNode(cafe.is_favorite ? "Quitar de favoritas" : "Agregar a favoritas"),
  );
  media.append(favorite);
  return media;
}

function ratingList(cafe) {
  const list = element("dl", "ratings");
  RATING_LABELS.forEach(([field, label]) => {
    const row = element("div", "rating-row");
    row.append(
      element("dt", "", label),
      element("dd", "", cafe[field] === null ? "Sin calificar" : `${cafe[field]}/5`),
    );
    list.append(row);
  });
  return list;
}

function actionButton(label, action, id, className = "button button-quiet", iconName) {
  const button = element("button", className);
  button.type = "button";
  button.dataset.action = action;
  button.dataset.id = id;
  button.append(icon(iconName), document.createTextNode(label));
  return button;
}

function cafeCard(cafe) {
  const card = element("article", "cafe-card");
  card.dataset.cafeId = cafe.id;
  card.append(cardMedia(cafe));

  const body = element("div", "card-body");
  const meta = element("div", "card-meta");
  const visited = cafe.visit_status === "VISITED";
  meta.append(
    element("span", `badge ${visited ? "badge-visited" : "badge-pending"}`, visited ? "Visitada" : "Pendiente"),
    element("span", "neighborhood", cafe.neighborhood),
  );
  const title = element("h3", "", cafe.name);
  const description = element(
    "p",
    cafe.description ? "description" : "description description-empty",
    cafe.description || "Sin descripción.",
  );
  const actions = element("div", "card-actions");
  actions.append(
    actionButton("Visitas", "visits", cafe.id, "button button-primary", "visits"),
    actionButton("Editar", "edit", cafe.id, "button button-quiet", "edit"),
    actionButton("Eliminar", "delete", cafe.id, "button button-destructive-quiet", "delete"),
  );
  body.append(meta, title, description, ratingList(cafe), actions);
  card.append(body);
  return card;
}

export function renderCafes(cafes, hasFilters) {
  const grid = document.querySelector("#cafe-grid");
  const empty = document.querySelector("#empty-state");
  const emptyTitle = document.querySelector("#empty-title");
  const emptyDescription = document.querySelector("#empty-description");
  const emptyAction = document.querySelector("#empty-action");
  grid.replaceChildren(...cafes.map(cafeCard));
  grid.setAttribute("aria-busy", "false");
  document.querySelector("#result-count").textContent = `${cafes.length} ${cafes.length === 1 ? "cafetería" : "cafeterías"}`;
  empty.hidden = cafes.length !== 0;
  if (cafes.length === 0 && hasFilters) {
    emptyTitle.textContent = "No hay cafeterías con esos filtros";
    emptyDescription.textContent = "Probá con otros criterios o limpiá la búsqueda.";
    emptyAction.textContent = "Limpiar filtros";
    emptyAction.dataset.action = "clear";
  } else {
    emptyTitle.textContent = "Todavía no registraste cafeterías";
    emptyDescription.textContent = "Agregá la primera parada de tu recorrido.";
    emptyAction.textContent = "Agregar cafetería";
    emptyAction.dataset.action = "add";
  }
}

function neighborhoodGroup(label, names) {
  const group = document.createElement("optgroup");
  group.label = label;
  group.append(...names.map((name) => {
    const option = element("option", "", name);
    option.value = name;
    return option;
  }));
  return group;
}

export function populateNeighborhoods(catalog, selected) {
  const select = document.querySelector("#neighborhood-filter");
  const first = element("option", "", "Todos los barrios");
  first.value = "";
  const groups = [neighborhoodGroup("Barrios oficiales", catalog.official)];
  if (catalog.historical.length) {
    groups.push(neighborhoodGroup("Valores históricos", catalog.historical));
  }
  select.replaceChildren(first, ...groups);
  select.value = selected || "";
}

export function setListState(message, { error = false, loading = false } = {}) {
  const status = document.querySelector("#list-status");
  const grid = document.querySelector("#cafe-grid");
  status.textContent = message;
  status.hidden = !message;
  status.classList.toggle("error", error);
  grid.setAttribute("aria-busy", String(loading));
  document.querySelector("#retry-load").hidden = !error;
}
