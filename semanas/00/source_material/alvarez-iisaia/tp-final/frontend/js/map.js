const DEFAULT_CENTER = { lat: -34.6037, lng: -58.3816 };
let currentPosition = null;
let mapInstance = null;
let markers = [];
let mapClickListener = null;
let placeSelectionHandler = null;


export function getCurrentPositionForView() {
  return currentPosition ? { ...currentPosition } : null;
}


export function clearCurrentPosition() {
  currentPosition = null;
}


export function requestCurrentPosition(geolocation = navigator.geolocation) {
  return new Promise((resolve, reject) => {
    if (!geolocation) {
      reject(new Error("La geolocalización no está disponible en este navegador."));
      return;
    }
    geolocation.getCurrentPosition(
      ({ coords }) => {
        currentPosition = { latitude: coords.latitude, longitude: coords.longitude };
        resolve(getCurrentPositionForView());
      },
      (error) => {
        const messages = {
          1: "No se concedió permiso para usar tu ubicación.",
          2: "No se pudo determinar tu ubicación.",
          3: "La ubicación tardó demasiado en responder.",
        };
        reject(new Error(messages[error.code] || "No se pudo obtener tu ubicación."));
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 0 },
    );
  });
}


export function loadMapsScript(config, documentObject = document) {
  if (!config.google_maps_enabled) return Promise.resolve(false);
  if (globalThis.google?.maps) return Promise.resolve(true);
  return new Promise((resolve, reject) => {
    const callbackName = `coffeeAtlasMapsReady${Date.now()}`;
    globalThis[callbackName] = () => {
      delete globalThis[callbackName];
      resolve(true);
    };
    const script = documentObject.createElement("script");
    const params = new URLSearchParams({
      key: config.google_maps_browser_key,
      map_ids: config.google_map_id,
      libraries: "places,marker",
      callback: callbackName,
      loading: "async",
      v: "weekly",
    });
    script.src = `https://maps.googleapis.com/maps/api/js?${params}`;
    script.async = true;
    script.onerror = () => reject(new Error("No se pudo cargar Google Maps."));
    documentObject.head.append(script);
  });
}


function clearMarkers() {
  markers.forEach((marker) => { marker.map = null; });
  markers = [];
}


function addMarker(position, title, maps = globalThis.google?.maps) {
  const AdvancedMarker = maps?.marker?.AdvancedMarkerElement;
  if (!AdvancedMarker || !mapInstance) return;
  markers.push(new AdvancedMarker({ map: mapInstance, position, title }));
}


export function renderAtlasMap(
  element,
  cafes,
  config,
  { onPlaceSelected = null } = {},
  maps = globalThis.google?.maps,
) {
  if (!config.google_maps_enabled || !maps?.Map) {
    element.replaceChildren();
    element.setAttribute("data-map-state", "unavailable");
    return false;
  }
  mapInstance = mapInstance || new maps.Map(element, {
    center: DEFAULT_CENTER,
    zoom: 12,
    mapId: config.google_map_id,
    streetViewControl: false,
    mapTypeControl: false,
  });
  placeSelectionHandler = onPlaceSelected;
  if (!mapClickListener && typeof mapInstance.addListener === "function") {
    mapClickListener = mapInstance.addListener("click", (event) => {
      if (!event.placeId || !placeSelectionHandler) return;
      event.stop?.();
      placeSelectionHandler(event.placeId);
    });
  }
  clearMarkers();
  cafes
    .filter((cafe) => cafe.location_status === "VERIFIED" && cafe.latitude !== null && cafe.longitude !== null)
    .forEach((cafe) => addMarker({ lat: cafe.latitude, lng: cafe.longitude }, cafe.name, maps));
  if (currentPosition) {
    addMarker(
      { lat: currentPosition.latitude, lng: currentPosition.longitude },
      "Tu ubicación actual",
      maps,
    );
  }
  element.setAttribute("data-map-state", "ready");
  return true;
}
