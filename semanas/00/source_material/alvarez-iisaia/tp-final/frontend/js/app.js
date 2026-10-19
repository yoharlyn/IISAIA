import { createCafe, deleteCafe, getConfig, getNeighborhoods, getProfile, listCafes, prepareCafe, searchRecommendations, updateCafe, updateProfile } from "./api.js";
import { populateNeighborhoods, renderCafes, setListState } from "./ui.js";
import { initializeSession } from "./auth.js";
import { getCurrentPositionForView, loadMapsScript, renderAtlasMap, requestCurrentPosition } from "./map.js";
import { mountPlaceAutocomplete, showAutocompleteUnavailable } from "./places.js";
import { renderRecommendations, renderRecommendationsUnavailable } from "./recommendations.js";
import { initializeVisits } from "./visits.js";
import { initializeDashboard } from "./dashboard.js";

const filterForm = document.querySelector("#filter-form");
const cafeDialog = document.querySelector("#cafe-dialog");
const cafeForm = document.querySelector("#cafe-form");
const deleteDialog = document.querySelector("#delete-dialog");
const deleteForm = document.querySelector("#delete-form");
const saveButton = document.querySelector("#save-cafe");
const deleteButton = document.querySelector("#confirm-delete");
const formError = document.querySelector("#form-error");
const deleteError = document.querySelector("#delete-error");
const mapStatus = document.querySelector("#map-status");
const mapPlaceSelection = document.querySelector("#map-place-selection");
const mapPlaceAction = document.querySelector("#map-place-action");

let cafesById = new Map();
let cafeToDelete = null;
let returnFocus = null;
let messageTimer = null;
let mapConfig = { google_maps_enabled: false };
let allCafesForMap = [];
let cafeSelection = null;
let homeSelection = null;
let mapPreparedCafe = null;
let cafeAutocomplete = null;

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
    const [cafes, allCafes, neighborhoods] = await Promise.all([
      listCafes(filters),
      listCafes(),
      getNeighborhoods(),
    ]);
    cafesById = new Map(cafes.map((cafe) => [String(cafe.id), cafe]));
    allCafesForMap = allCafes;
    renderCafes(cafes, hasFilters(filters));
    populateNeighborhoods(neighborhoods, filters.neighborhood);
    renderCurrentMap();
    setListState("");
  } catch (error) {
    setListState(error.message, { error: true });
  }
}

async function initializeMap() {
  const status = mapStatus;
  try {
    mapConfig = await getConfig();
    if (!mapConfig.google_maps_enabled) {
      status.textContent = "Mapa no disponible: Google Maps todavía no está configurado.";
      initializeAutocompletes();
      return;
    }
    await loadMapsScript(mapConfig);
    initializeAutocompletes();
    renderCurrentMap();
    status.textContent = "Mapa listo. Las ubicaciones vencidas no se muestran.";
  } catch (error) {
    renderRecommendationsUnavailable(document.querySelector("#recommendations-list"), error.message);
    status.textContent = error.message;
    status.classList.add("error");
  }
}

function initializeAutocompletes() {
  if (!mapConfig.google_maps_enabled) {
    showAutocompleteUnavailable(document.querySelector("#cafe-autocomplete"), "No podés agregar ubicaciones nuevas hasta configurar Google Maps.");
    showAutocompleteUnavailable(document.querySelector("#home-autocomplete"), "El domicilio no puede verificarse sin Google Maps.");
    showAutocompleteUnavailable(document.querySelector("#map-place-autocomplete"), "La búsqueda de cafeterías requiere Google Maps.");
    return;
  }
  cafeAutocomplete = mountPlaceAutocomplete(
    document.querySelector("#cafe-autocomplete"),
    async (selection) => {
      document.querySelector("#cafe-address-selection").textContent = "Verificando la ubicación…";
      const prepared = await prepareCafe(selection.place_id);
      if (prepared.already_saved) {
        throw new Error("Esta cafetería ya está en tu atlas.");
      }
      applyPreparedCafe(prepared);
    },
    globalThis.google,
    {
      label: "Buscar una dirección de cafetería en CABA",
      onError: showCafePreparationError,
    },
  );
  mountPlaceAutocomplete(document.querySelector("#home-autocomplete"), (selection) => {
    homeSelection = selection;
    document.querySelector("#home-address-selection").textContent = `Seleccionada: ${selection.selected_address}`;
  });
  mountPlaceAutocomplete(
    document.querySelector("#map-place-autocomplete"),
    (selection) => prepareMapPlace(selection.place_id),
    globalThis.google,
    {
      label: "Buscar una cafetería en CABA",
      onError: (error) => setMapStatus(error.message, true),
    },
  );
}

function renderCurrentMap() {
  renderAtlasMap(
    document.querySelector("#atlas-map"),
    allCafesForMap,
    mapConfig,
    { onPlaceSelected: (placeId) => prepareMapPlace(placeId) },
  );
}

async function loadProfile() {
  const profile = await getProfile();
  document.querySelector("#profile-display-name").value = profile.display_name;
  document.querySelector("#home-address-selection").textContent = profile.home_selected_address
    ? `Domicilio guardado: ${profile.home_selected_address}`
    : "No configuraste un domicilio.";
}

async function saveProfile(event) {
  event.preventDefault();
  const button = document.querySelector("#save-profile");
  const status = document.querySelector("#profile-status");
  button.disabled = true;
  try {
    const payload = { display_name: document.querySelector("#profile-display-name").value };
    if (homeSelection) payload.home = homeSelection;
    await updateProfile(payload);
    homeSelection = null;
    status.textContent = "Perfil guardado.";
    await loadProfile();
  } catch (error) {
    status.textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

async function findRecommendations(event) {
  event.preventDefault();
  const status = document.querySelector("#recommendations-status");
  const data = new FormData(event.currentTarget);
  const type = data.get("origin");
  let origin = { type };
  status.classList.remove("error");
  status.textContent = "Buscando recomendaciones…";
  try {
    if (type === "current") {
      let position = getCurrentPositionForView();
      if (!position) position = await requestCurrentPosition();
      origin = { type, ...position };
    }
    const items = await searchRecommendations({ origin, radius_km: Number(data.get("radius_km")) });
    renderRecommendations(document.querySelector("#recommendations-list"), items);
    status.textContent = `${items.length} recomendaciones. Datos actuales: Google Maps.`;
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
    renderCurrentMap();
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

function setFormValue(name, value) {
  cafeForm.elements[name].value = value ?? "";
}

function setMapStatus(message, isError = false) {
  mapStatus.textContent = message;
  mapStatus.classList.toggle("error", isError);
}

function showCafePreparationError(error) {
  cafeSelection = null;
  formError.textContent = error.message;
  formError.hidden = false;
  formError.tabIndex = -1;
  formError.focus();
  document.querySelector("#cafe-address-selection").textContent = "Elegí otro resultado para volver a intentar.";
}

function applyPreparedCafe(prepared) {
  cafeSelection = {
    place_id: prepared.place_id,
    selected_address: prepared.formatted_address,
  };
  setFormValue("place_id", prepared.place_id);
  setFormValue("selected_address", prepared.formatted_address);
  setFormValue("name", prepared.display_name);
  cafeForm.elements.name.readOnly = true;
  document.querySelector("#cafe-location-field").hidden = true;
  document.querySelector("#cafe-prepared-location").hidden = false;
  document.querySelector("#cafe-prepared-address").textContent = prepared.formatted_address;
  document.querySelector("#cafe-prepared-neighborhood").textContent = prepared.neighborhood;
  formError.hidden = true;
  saveButton.disabled = false;
  if (cafeDialog.open) cafeForm.elements.description.focus();
}

function renderMapPreparedCafe(prepared) {
  mapPreparedCafe = prepared;
  document.querySelector("#map-place-selection-title").textContent = prepared.display_name;
  document.querySelector("#map-place-address").textContent = prepared.formatted_address;
  document.querySelector("#map-place-neighborhood").textContent = prepared.neighborhood;
  mapPlaceAction.textContent = prepared.already_saved
    ? "Abrir ficha en mi atlas"
    : "Agregar a mis cafeterías";
  mapPlaceSelection.hidden = false;
  setMapStatus(
    prepared.already_saved
      ? "Ya está en tu atlas. Podés abrir su ficha."
      : "Lugar verificado. Revisá los datos y elegí si querés agregarlo.",
  );
  mapPlaceAction.focus();
}

async function prepareMapPlace(placeId) {
  mapPreparedCafe = null;
  mapPlaceSelection.hidden = true;
  setMapStatus("Verificando el lugar seleccionado…");
  try {
    renderMapPreparedCafe(await prepareCafe(placeId));
  } catch (error) {
    setMapStatus(error.message, true);
  }
}

async function prepareAndOpenCafe(placeId, trigger) {
  const originalText = trigger.textContent;
  trigger.disabled = true;
  trigger.textContent = "Verificando…";
  try {
    const prepared = await prepareCafe(placeId);
    if (prepared.already_saved) {
      const existing = allCafesForMap.find((cafe) => cafe.id === prepared.existing_cafe_id);
      if (existing) {
        showMessage("Ya está en tu atlas. Abrimos su ficha.");
        openCafeForm(existing, trigger);
      } else {
        showMessage("Ya está en tu atlas.");
      }
      return;
    }
    openCafeForm(null, trigger, prepared);
  } catch (error) {
    showMessage(error.message);
  } finally {
    trigger.disabled = false;
    trigger.textContent = originalText;
  }
}

function resetPreparedCafe() {
  cafeSelection = null;
  setFormValue("place_id", "");
  setFormValue("selected_address", "");
  if (!cafeForm.elements.id.value) setFormValue("name", "");
  cafeForm.elements.name.readOnly = Boolean(!cafeForm.elements.id.value);
  document.querySelector("#cafe-location-field").hidden = false;
  document.querySelector("#cafe-prepared-location").hidden = true;
  document.querySelector("#cafe-address-selection").textContent = cafeForm.elements.id.value
    ? "Elegí una dirección de la lista para cambiar la ubicación."
    : "Seleccioná una dirección de la lista para continuar.";
  saveButton.disabled = !cafeForm.elements.id.value;
  cafeAutocomplete?.focus();
}

function openCafeForm(cafe = null, trigger = document.activeElement, prepared = null) {
  returnFocus = trigger;
  cafeForm.reset();
  formError.hidden = true;
  formError.textContent = "";
  document.querySelector("#cafe-dialog-title").textContent = cafe ? "Editar cafetería" : "Agregar cafetería";
  setFormValue("id", cafe?.id);
  setFormValue("name", cafe?.name || "");
  setFormValue("description", cafe?.description);
  setFormValue("image_url", cafe?.image_url);
  cafeSelection = null;
  setFormValue("place_id", "");
  setFormValue("selected_address", "");
  document.querySelector("#cafe-address-selection").textContent = cafe?.selected_address
    ? `Dirección guardada: ${cafe.selected_address}. Elegí otra para cambiarla.`
    : "Seleccioná una dirección de la lista para continuar.";
  cafeForm.elements.is_favorite.checked = cafe?.is_favorite || false;
  cafeForm.elements.name.readOnly = !cafe;
  document.querySelector("#cafe-location-field").hidden = false;
  document.querySelector("#cafe-prepared-location").hidden = true;
  if (prepared) applyPreparedCafe(prepared);
  else saveButton.disabled = !cafe;
  cafeDialog.showModal();
  if (prepared || cafe) {
    (prepared ? cafeForm.elements.description : cafeForm.elements.name).focus();
  } else {
    cafeAutocomplete?.focus();
  }
}

function closeDialog(dialog) {
  dialog.close();
}

function formPayload(isEditing) {
  const data = new FormData(cafeForm);
  const description = data.get("description").trim();
  const payload = {
    name: data.get("name"),
    description: description || null,
    image_url: data.get("image_url").trim() || null,
    is_favorite: data.get("is_favorite") === "on",
  };
  if (cafeSelection) Object.assign(payload, cafeSelection);
  if (!isEditing && !cafeSelection) {
    throw new Error("Seleccioná una dirección con el autocompletado.");
  }
  return payload;
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
    await (id ? updateCafe(id, formPayload(true)) : createCafe(formPayload(false)));
    closeDialog(cafeDialog);
    showMessage(id ? "Cafetería actualizada." : "Cafetería agregada al atlas.");
    await loadData();
  } catch (error) {
    formError.textContent = error.message;
    formError.hidden = false;
    formError.tabIndex = -1;
    formError.focus();
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
  if (button.dataset.action === "visits") visits.open(cafe, button);
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
document.querySelector("#profile-form").addEventListener("submit", saveProfile);
document.querySelector("#recommendations-form").addEventListener("submit", findRecommendations);
document.addEventListener("coffee-atlas:prepare-recommendation", (event) => {
  prepareAndOpenCafe(event.detail.item.place_id, event.detail.trigger);
});
document.querySelector("#change-cafe-location").addEventListener("click", resetPreparedCafe);
mapPlaceAction.addEventListener("click", () => {
  if (!mapPreparedCafe) return;
  if (mapPreparedCafe.already_saved) {
    const existing = allCafesForMap.find(
      (cafe) => cafe.id === mapPreparedCafe.existing_cafe_id,
    );
    if (existing) openCafeForm(existing, mapPlaceAction);
    return;
  }
  openCafeForm(null, mapPlaceAction, mapPreparedCafe);
});
[cafeDialog, deleteDialog].forEach((dialog) => dialog.addEventListener("close", () => returnFocus?.focus()));

const dashboard = initializeDashboard();
const visits = initializeVisits({
  onChanged: () => Promise.all([loadData(), dashboard.load()]),
  announce: showMessage,
});
initializeSession(async () => {
  await Promise.all([loadData(), loadProfile(), dashboard.load()]);
  await initializeMap();
});
