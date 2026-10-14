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

  const favorite = element(
    "button",
    "favorite-button",
    cafe.is_favorite ? "Quitar de favoritas" : "Agregar a favoritas",
  );
  favorite.type = "button";
  favorite.dataset.action = "toggle-favorite";
  favorite.dataset.id = cafe.id;
  favorite.setAttribute("aria-pressed", String(cafe.is_favorite));
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

function actionButton(label, action, id, className = "button button-quiet") {
  const button = element("button", className, label);
  button.type = "button";
  button.dataset.action = action;
  button.dataset.id = id;
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
  const description = element("p", "description", cafe.description);
  const actions = element("div", "card-actions");
  actions.append(
    actionButton("Visitas", "visits", cafe.id, "button button-primary"),
    actionButton("Editar", "edit", cafe.id),
    actionButton("Eliminar", "delete", cafe.id, "button button-danger"),
  );
  body.append(meta, title, description, ratingList(cafe), actions);
  card.append(body);
  return card;
}

export function renderStats(stats) {
  document.querySelector("#stat-total").textContent = stats.total;
  document.querySelector("#stat-visited").textContent = stats.visited;
  document.querySelector("#stat-pending").textContent = stats.pending;
  document.querySelector("#stat-favorites").textContent = stats.favorites;
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

export function populateNeighborhoods(cafes, selected) {
  const select = document.querySelector("#neighborhood-filter");
  const first = element("option", "", "Todos los barrios");
  first.value = "";
  const neighborhoods = [...new Set(cafes.map((cafe) => cafe.neighborhood))]
    .sort((a, b) => a.localeCompare(b, "es"));
  const options = neighborhoods.map((name) => {
    const option = element("option", "", name);
    option.value = name;
    return option;
  });
  select.replaceChildren(first, ...options);
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
