import { createCafe, deleteCafe, getConfig, getStats, listCafes, updateCafe } from "./api.js";
import { populateNeighborhoods, renderCafes, renderStats, setListState } from "./ui.js";
import { initializeSession } from "./auth.js";
import { loadMapsScript, renderAtlasMap, requestCurrentPosition } from "./map.js";

const filterForm = document.querySelector("#filter-form");
const cafeDialog = document.querySelector("#cafe-dialog");
const cafeForm = document.querySelector("#cafe-form");
const deleteDialog = document.querySelector("#delete-dialog");
const deleteForm = document.querySelector("#delete-form");
const saveButton = document.querySelector("#save-cafe");
const deleteButton = document.querySelector("#confirm-delete");
const formError = document.querySelector("#form-error");
const deleteError = document.querySelector("#delete-error");

let cafesById = new Map();
let cafeToDelete = null;
let returnFocus = null;
let messageTimer = null;
let mapConfig = { google_maps_enabled: false };
let allCafesForMap = [];

function currentFilters() {
  const data = new FormData(filterForm);
  return {
    q: data.get("q").trim(),
    neighborhood: data.get("neighborhood"),
    visit_status: data.get("visit_status"),
    is_favorite: data.get("is_favorite") === "on" ? "true" : "",
  };
}

function hasFilters(filters) {
  return Object.values(filters).some(Boolean);
}

async function loadData() {
  const filters = currentFilters();
  setListState("Cargando cafeterías…", { loading: true });
  try {
    const [cafes, allCafes, stats] = await Promise.all([
      listCafes(filters),
      listCafes(),
      getStats(),
    ]);
    cafesById = new Map(cafes.map((cafe) => [String(cafe.id), cafe]));
    allCafesForMap = allCafes;
    renderCafes(cafes, hasFilters(filters));
    populateNeighborhoods(allCafes, filters.neighborhood);
    renderStats(stats);
    renderAtlasMap(document.querySelector("#atlas-map"), allCafesForMap, mapConfig);
    setListState("");
  } catch (error) {
    setListState(error.message, { error: true });
  }
}

async function initializeMap() {
  const status = document.querySelector("#map-status");
  try {
    mapConfig = await getConfig();
    if (!mapConfig.google_maps_enabled) {
      status.textContent = "Mapa no disponible: Google Maps todavía no está configurado.";
      return;
    }
    await loadMapsScript(mapConfig);
    renderAtlasMap(document.querySelector("#atlas-map"), allCafesForMap, mapConfig);
    status.textContent = "Mapa listo. Las ubicaciones vencidas no se muestran.";
  } catch (error) {
    status.textContent = error.message;
  }
}

async function locateUser() {
  const button = document.querySelector("#locate-user");
  const status = document.querySelector("#map-status");
  button.disabled = true;
  status.textContent = "Solicitando tu ubicación…";
  try {
    await requestCurrentPosition();
    renderAtlasMap(document.querySelector("#atlas-map"), allCafesForMap, mapConfig);
    status.textContent = "Tu ubicación se usa sólo en esta vista y no se guarda.";
  } catch (error) {
    status.textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

function showMessage(message) {
  const region = document.querySelector("#global-message");
  window.clearTimeout(messageTimer);
  region.textContent = message;
  messageTimer = window.setTimeout(() => { region.textContent = ""; }, 4500);
}

function fillRatings() {
  ["coffee", "food", "ambience", "service"].forEach((name) => {
    const select = document.querySelector(`#${name}-rating`);
    const empty = document.createElement("option");
    empty.value = "";
    empty.textContent = "Sin calificar";
    const options = [1, 2, 3, 4, 5].map((rating) => {
      const option = document.createElement("option");
      option.value = rating;
      option.textContent = `${rating} de 5`;
      return option;
    });
    select.replaceChildren(empty, ...options);
  });
}

function setFormValue(name, value) {
  cafeForm.elements[name].value = value ?? "";
}

function openCafeForm(cafe = null, trigger = document.activeElement) {
  returnFocus = trigger;
  cafeForm.reset();
  formError.hidden = true;
  formError.textContent = "";
  document.querySelector("#cafe-dialog-title").textContent = cafe ? "Editar cafetería" : "Agregar cafetería";
  setFormValue("id", cafe?.id);
  setFormValue("name", cafe?.name);
  setFormValue("neighborhood", cafe?.neighborhood);
  setFormValue("description", cafe?.description);
  setFormValue("image_url", cafe?.image_url);
  setFormValue("visit_status", cafe?.visit_status || "PENDING");
  cafeForm.elements.is_favorite.checked = cafe?.is_favorite || false;
  ["coffee_rating", "food_rating", "ambience_rating", "service_rating"].forEach((field) => setFormValue(field, cafe?.[field]));
  cafeDialog.showModal();
  cafeForm.elements.name.focus();
}

function closeDialog(dialog) {
  dialog.close();
}

function formPayload() {
  const data = new FormData(cafeForm);
  const rating = (name) => data.get(name) === "" ? null : Number(data.get(name));
  return {
    name: data.get("name"),
    neighborhood: data.get("neighborhood"),
    description: data.get("description"),
    image_url: data.get("image_url").trim() || null,
    visit_status: data.get("visit_status"),
    is_favorite: data.get("is_favorite") === "on",
    coffee_rating: rating("coffee_rating"),
    food_rating: rating("food_rating"),
    ambience_rating: rating("ambience_rating"),
    service_rating: rating("service_rating"),
  };
}

async function saveCafe(event) {
  event.preventDefault();
  if (!cafeForm.checkValidity()) {
    cafeForm.reportValidity();
    return;
  }
  saveButton.disabled = true;
  saveButton.textContent = "Guardando…";
  formError.hidden = true;
  try {
    const id = cafeForm.elements.id.value;
    await (id ? updateCafe(id, formPayload()) : createCafe(formPayload()));
    closeDialog(cafeDialog);
    showMessage(id ? "Cafetería actualizada." : "Cafetería agregada al atlas.");
    await loadData();
  } catch (error) {
    formError.textContent = error.message;
    formError.hidden = false;
  } finally {
    saveButton.disabled = false;
    saveButton.textContent = "Guardar cafetería";
  }
}

function openDelete(cafe, trigger) {
  cafeToDelete = cafe;
  returnFocus = trigger;
  deleteError.hidden = true;
  document.querySelector("#delete-message").textContent = `Vas a eliminar ${cafe.name}. Esta acción no se puede deshacer.`;
  deleteDialog.showModal();
  document.querySelector("#cancel-delete").focus();
}

async function confirmDelete(event) {
  event.preventDefault();
  if (!cafeToDelete) return;
  deleteButton.disabled = true;
  deleteButton.textContent = "Eliminando…";
  deleteError.hidden = true;
  try {
    await deleteCafe(cafeToDelete.id);
    closeDialog(deleteDialog);
    showMessage("Cafetería eliminada.");
    cafeToDelete = null;
    await loadData();
  } catch (error) {
    deleteError.textContent = error.message;
    deleteError.hidden = false;
  } finally {
    deleteButton.disabled = false;
    deleteButton.textContent = "Eliminar definitivamente";
  }
}

async function handleCardAction(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const cafe = cafesById.get(button.dataset.id);
  if (!cafe) return;
  if (button.dataset.action === "edit") openCafeForm(cafe, button);
  if (button.dataset.action === "delete") openDelete(cafe, button);
  if (button.dataset.action === "toggle-favorite") {
    button.disabled = true;
    try {
      await updateCafe(cafe.id, { is_favorite: !cafe.is_favorite });
      showMessage(cafe.is_favorite ? "Se quitó de favoritas." : "Se agregó a favoritas.");
      await loadData();
    } catch (error) {
      showMessage(error.message);
      button.disabled = false;
    }
  }
}

function clearFilters() {
  filterForm.reset();
  loadData();
}

filterForm.addEventListener("submit", (event) => { event.preventDefault(); loadData(); });
cafeForm.addEventListener("submit", saveCafe);
deleteForm.addEventListener("submit", confirmDelete);
document.querySelector("#cafe-grid").addEventListener("click", handleCardAction);
document.querySelector("#add-cafe").addEventListener("click", (event) => openCafeForm(null, event.currentTarget));
document.querySelector("#empty-action").addEventListener("click", (event) => event.currentTarget.dataset.action === "clear" ? clearFilters() : openCafeForm(null, event.currentTarget));
document.querySelector("#clear-filters").addEventListener("click", clearFilters);
document.querySelector("#retry-load").addEventListener("click", loadData);
document.querySelector("#close-cafe-dialog").addEventListener("click", () => closeDialog(cafeDialog));
document.querySelector("#cancel-cafe").addEventListener("click", () => closeDialog(cafeDialog));
document.querySelector("#cancel-delete").addEventListener("click", () => closeDialog(deleteDialog));
document.querySelector("#locate-user").addEventListener("click", locateUser);
[cafeDialog, deleteDialog].forEach((dialog) => dialog.addEventListener("close", () => returnFocus?.focus()));

fillRatings();
initializeSession(async () => {
  await loadData();
  await initializeMap();
});
