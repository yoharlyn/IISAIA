import {
  createVisit,
  deleteVisit,
  deleteVisitPhoto,
  listVisits,
  updateVisit,
  uploadVisitPhoto,
} from "./api.js";

const MAX_FILE_BYTES = 5 * 1024 * 1024;
const MAX_VISIT_BYTES = 20 * 1024 * 1024;
const MAX_PHOTOS = 5;
const ALLOWED_MIME = new Set(["image/jpeg", "image/png", "image/webp"]);
const RATING_FIELDS = [
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

function button(label, action, id, className = "button button-quiet") {
  const node = element("button", className, label);
  node.type = "button";
  node.dataset.action = action;
  node.dataset.id = id;
  return node;
}

function formatDate(value, estimated) {
  const formatted = new Intl.DateTimeFormat("es-AR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
  return estimated ? `${formatted} (fecha estimada)` : formatted;
}

function localDateTimeValue(value) {
  const date = value ? new Date(value) : new Date();
  const pad = (part) => String(part).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function ratingSummary(visit) {
  const list = element("dl", "visit-ratings");
  RATING_FIELDS.forEach(([field, label]) => {
    const row = element("div", "rating-row");
    row.append(
      element("dt", "", label),
      element("dd", "", visit[field] === null ? "Sin calificar" : `${visit[field]}/5`),
    );
    list.append(row);
  });
  return list;
}

function photoCard(photo) {
  const card = element("figure", "visit-photo");
  const media = element("div", "visit-photo-media");
  const image = document.createElement("img");
  image.src = photo.url;
  image.alt = photo.caption;
  image.loading = "lazy";
  image.width = photo.width;
  image.height = photo.height;
  const fallback = element("p", "photo-fallback", "La fotografía no está disponible.");
  fallback.hidden = true;
  image.addEventListener("error", () => {
    image.hidden = true;
    fallback.hidden = false;
  }, { once: true });
  media.append(image, fallback);
  const caption = element("figcaption", "", photo.caption);
  const remove = button("Eliminar foto", "delete-photo", photo.id, "button button-destructive-quiet");
  card.append(media, caption, remove);
  return card;
}

function photoForm(visit) {
  const form = element("form", "photo-form");
  form.dataset.visitId = visit.id;
  const fileField = element("div", "field");
  const fileLabel = element("label", "", "Fotografía");
  const file = document.createElement("input");
  file.type = "file";
  file.name = "file";
  file.accept = "image/jpeg,image/png,image/webp";
  file.required = true;
  fileLabel.htmlFor = `visit-photo-${visit.id}`;
  file.id = fileLabel.htmlFor;
  fileField.append(fileLabel, file);
  const captionField = element("div", "field");
  const captionLabel = element("label", "", "Descripción accesible");
  const caption = document.createElement("input");
  caption.type = "text";
  caption.name = "caption";
  caption.required = true;
  caption.maxLength = 200;
  caption.id = `visit-photo-caption-${visit.id}`;
  captionLabel.htmlFor = caption.id;
  captionField.append(captionLabel, caption);
  const submit = element("button", "button button-quiet", "Subir fotografía");
  submit.type = "submit";
  form.append(fileField, captionField, submit);
  return form;
}

function visitCard(visit) {
  const card = element("article", "visit-card");
  card.dataset.visitId = visit.id;
  const heading = element("div", "visit-heading");
  const title = element("h3", "", formatDate(visit.visited_at, visit.date_is_estimated));
  const actions = element("div", "visit-actions");
  actions.append(
    button("Editar visita", "edit-visit", visit.id),
    button("Eliminar visita", "delete-visit", visit.id, "button button-destructive-quiet"),
  );
  heading.append(title, actions);
  card.append(heading);
  if (visit.note) card.append(element("p", "visit-note", visit.note));
  card.append(ratingSummary(visit));

  const photosHeading = element("h4", "", `Fotografías (${visit.photos.length}/${MAX_PHOTOS})`);
  const gallery = element("div", "visit-gallery");
  gallery.replaceChildren(...visit.photos.map(photoCard));
  card.append(photosHeading, gallery);
  if (visit.photos.length < MAX_PHOTOS) card.append(photoForm(visit));
  else card.append(element("p", "limit-note", "Alcanzaste el máximo de 5 fotografías para esta visita."));
  return card;
}

function visitPayload(form) {
  const data = new FormData(form);
  const rating = (name) => data.get(name) === "" ? null : Number(data.get(name));
  return {
    visited_at: new Date(data.get("visited_at")).toISOString(),
    note: data.get("note").trim() || null,
    coffee_rating: rating("coffee_rating"),
    food_rating: rating("food_rating"),
    ambience_rating: rating("ambience_rating"),
    service_rating: rating("service_rating"),
    date_is_estimated: data.get("date_is_estimated") === "on",
  };
}

function validatePhoto(file, visit) {
  if (!ALLOWED_MIME.has(file.type)) return "El formato debe ser JPEG, PNG o WebP.";
  if (file.size > MAX_FILE_BYTES) return "La fotografía supera el límite de 5 MiB.";
  if (visit.photos.length >= MAX_PHOTOS) return "Cada visita admite hasta 5 fotografías.";
  const used = visit.photos.reduce((total, photo) => total + photo.size_bytes, 0);
  if (used + file.size > MAX_VISIT_BYTES) return "Las fotografías superan el límite acumulado de 20 MiB.";
  return null;
}

export function initializeVisits({ onChanged, announce }) {
  const dialog = document.querySelector("#visit-dialog");
  const form = document.querySelector("#visit-form");
  const list = document.querySelector("#visit-list");
  const status = document.querySelector("#visit-status");
  const editor = document.querySelector("#visit-editor");
  const save = document.querySelector("#save-visit");
  let cafe = null;
  let visits = [];
  let returnFocus = null;

  function setStatus(message, error = false) {
    status.textContent = message;
    status.classList.toggle("error", error);
  }

  function resetEditor(visit = null) {
    form.reset();
    form.elements.id.value = visit?.id || "";
    form.elements.visited_at.value = localDateTimeValue(visit?.visited_at);
    form.elements.note.value = visit?.note || "";
    form.elements.date_is_estimated.checked = visit?.date_is_estimated || false;
    RATING_FIELDS.forEach(([field]) => { form.elements[field].value = visit?.[field] || ""; });
    document.querySelector("#visit-editor-title").textContent = visit ? "Editar visita" : "Registrar visita";
    save.textContent = visit ? "Guardar cambios" : "Registrar visita";
    editor.hidden = false;
    form.elements.visited_at.focus();
  }

  function render() {
    list.replaceChildren(...visits.map(visitCard));
    list.hidden = visits.length === 0;
    document.querySelector("#visit-empty").hidden = visits.length !== 0;
  }

  async function refresh() {
    setStatus("Cargando visitas…");
    try {
      visits = await listVisits(cafe.id);
      render();
      setStatus(`${visits.length} ${visits.length === 1 ? "visita registrada" : "visitas registradas"}.`);
    } catch (error) {
      setStatus(error.message, true);
    }
  }

  async function open(selectedCafe, trigger) {
    cafe = selectedCafe;
    returnFocus = trigger;
    editor.hidden = true;
    list.replaceChildren();
    document.querySelector("#visit-dialog-title").textContent = `Visitas a ${cafe.name}`;
    dialog.showModal();
    document.querySelector("#add-visit").focus();
    await refresh();
  }

  async function saveVisit(event) {
    event.preventDefault();
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }
    save.disabled = true;
    setStatus("Guardando visita…");
    try {
      const id = form.elements.id.value;
      await (id ? updateVisit(id, visitPayload(form)) : createVisit(cafe.id, visitPayload(form)));
      editor.hidden = true;
      announce(id ? "Visita actualizada." : "Visita registrada.");
      await Promise.all([refresh(), onChanged()]);
    } catch (error) {
      setStatus(error.message, true);
    } finally {
      save.disabled = false;
    }
  }

  async function submitPhoto(photoFormNode) {
    const visit = visits.find((item) => String(item.id) === photoFormNode.dataset.visitId);
    const data = new FormData(photoFormNode);
    const file = data.get("file");
    const error = validatePhoto(file, visit);
    if (error) {
      setStatus(error, true);
      return;
    }
    const submit = photoFormNode.querySelector("button[type='submit']");
    submit.disabled = true;
    submit.textContent = "Subiendo…";
    setStatus("Procesando y subiendo fotografía…");
    try {
      await uploadVisitPhoto(visit.id, file, data.get("caption").trim());
      announce("Fotografía agregada.");
      await refresh();
    } catch (uploadError) {
      setStatus(uploadError.message, true);
      submit.disabled = false;
      submit.textContent = "Subir fotografía";
    }
  }

  async function handleAction(event) {
    const action = event.target.closest("button[data-action]");
    if (!action) return;
    const visit = visits.find((item) => String(item.id) === action.dataset.id);
    if (action.dataset.action === "edit-visit") resetEditor(visit);
    if (action.dataset.action === "delete-visit") {
      if (!window.confirm("¿Querés eliminar esta visita y sus fotografías?")) return;
      action.disabled = true;
      setStatus("Eliminando visita…");
      try {
        await deleteVisit(action.dataset.id);
        announce("Visita eliminada.");
        await Promise.all([refresh(), onChanged()]);
      } catch (error) {
        setStatus(error.message, true);
        action.disabled = false;
      }
    }
    if (action.dataset.action === "delete-photo") {
      if (!window.confirm("¿Querés eliminar esta fotografía?")) return;
      action.disabled = true;
      setStatus("Eliminando fotografía…");
      try {
        await deleteVisitPhoto(action.dataset.id);
        announce("Fotografía eliminada.");
        await refresh();
      } catch (error) {
        setStatus(error.message, true);
        action.disabled = false;
      }
    }
  }

  form.addEventListener("submit", saveVisit);
  dialog.addEventListener("submit", (event) => {
    if (event.target.matches(".photo-form")) {
      event.preventDefault();
      submitPhoto(event.target);
    }
  });
  list.addEventListener("click", handleAction);
  document.querySelector("#add-visit").addEventListener("click", () => resetEditor());
  document.querySelector("#cancel-visit-edit").addEventListener("click", () => { editor.hidden = true; });
  document.querySelector("#close-visit-dialog").addEventListener("click", () => { dialog.close(); });
  dialog.addEventListener("close", () => returnFocus?.focus());
  return { open };
}
