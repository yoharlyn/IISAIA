function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function recommendationCard(item) {
  const card = element("article", "recommendation-card");
  if (item.opening_date) {
    card.append(element("p", "badge badge-pending", `Próxima apertura: ${item.opening_date}`));
  }
  card.append(
    element("h3", "", item.display_name || "Nombre no informado"),
    element("p", "", item.formatted_address || "Dirección no informada"),
    element("p", "recommendation-meta", `${item.distance_km.toFixed(1)} km · ${item.rating === null ? "Sin rating" : `${item.rating}/5`} · ${item.novelty_label}`),
    element("p", "recommendation-explanation", `Puntaje ${(item.score * 100).toFixed(0)}/100 según cercanía, datos disponibles y tu atlas.`),
    element("p", "google-attribution", "Datos actuales: Google Maps"),
  );
  const button = element("button", "button button-primary", "Preparar para guardar");
  button.type = "button";
  button.addEventListener("click", () => document.dispatchEvent(
    new CustomEvent("coffee-atlas:prepare-recommendation", { detail: item }),
  ));
  card.append(button);
  return card;
}

export function renderRecommendations(container, items) {
  container.replaceChildren(...items.map(recommendationCard));
  if (!items.length) {
    container.append(element("p", "empty-state", "No encontramos recomendaciones para ese radio."));
  }
}
