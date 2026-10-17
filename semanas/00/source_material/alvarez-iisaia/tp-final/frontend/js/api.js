const API_ROOT = "/api";
let csrfToken = null;

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function setCsrfToken(value) {
  csrfToken = value || null;
}

function validationMessage(detail) {
  if (!Array.isArray(detail)) return null;
  return detail.map((item) => item.msg?.replace(/^Value error, /, "") || "Dato inválido.").join(" ");
}

async function request(url, options = {}) {
  const config = { credentials: "same-origin", ...options, headers: { ...(options.headers || {}) } };
  if (config.body && !(config.body instanceof FormData)) {
    config.headers["Content-Type"] = "application/json";
  }
  if (csrfToken && !["GET", "HEAD"].includes(config.method || "GET")) {
    config.headers["X-CSRF-Token"] = csrfToken;
  }
  let response;
  try {
    response = await fetch(url, config);
  } catch {
    throw new ApiError("No pudimos conectar con Coffee Atlas. Revisá que el servidor esté activo.", 0);
  }
  if (response.status === 204) return null;
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = validationMessage(data?.detail) || data?.detail;
    const error = new ApiError(
      typeof detail === "string" ? detail : "La solicitud no pudo completarse.",
      response.status,
    );
    if (response.status === 401) window.dispatchEvent(new CustomEvent("coffee-atlas:session-expired"));
    throw error;
  }
  return data;
}

export const getSession = () => request(`${API_ROOT}/session`);
export const getConfig = () => request(`${API_ROOT}/config`);
export const getProfile = () => request(`${API_ROOT}/profile`);
export const updateProfile = (payload) => request(`${API_ROOT}/profile`, { method: "PATCH", body: JSON.stringify(payload) });

export async function logoutSession() {
  return request("/auth/logout", {
    method: "POST",
    headers: { Accept: "application/json" },
  });
}

export function listCafes(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== "" && value !== null && value !== undefined) params.set(key, value);
  });
  const query = params.toString();
  return request(`${API_ROOT}/cafes${query ? `?${query}` : ""}`);
}

export const createCafe = (payload) => request(`${API_ROOT}/cafes`, { method: "POST", body: JSON.stringify(payload) });
export const updateCafe = (id, payload) => request(`${API_ROOT}/cafes/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
export const deleteCafe = (id) => request(`${API_ROOT}/cafes/${id}`, { method: "DELETE" });
export const searchCafes = (payload) => request(`${API_ROOT}/cafes/search`, { method: "POST", body: JSON.stringify(payload) });
export const searchRecommendations = (payload) => request(`${API_ROOT}/recommendations/search`, { method: "POST", body: JSON.stringify(payload) });
export const prepareRecommendation = (placeId) => request(`${API_ROOT}/recommendations/${encodeURIComponent(placeId)}/prepare-save`, { method: "POST" });
export const listVisits = (cafeId) => request(`${API_ROOT}/cafes/${cafeId}/visits`);
export const createVisit = (cafeId, payload) => request(`${API_ROOT}/cafes/${cafeId}/visits`, { method: "POST", body: JSON.stringify(payload) });
export const updateVisit = (visitId, payload) => request(`${API_ROOT}/visits/${visitId}`, { method: "PATCH", body: JSON.stringify(payload) });
export const deleteVisit = (visitId) => request(`${API_ROOT}/visits/${visitId}`, { method: "DELETE" });
export function uploadVisitPhoto(visitId, file, caption) {
  const body = new FormData();
  body.append("file", file);
  body.append("caption", caption);
  return request(`${API_ROOT}/visits/${visitId}/photos`, { method: "POST", body });
}
export const deleteVisitPhoto = (photoId) => request(`${API_ROOT}/photos/${photoId}`, { method: "DELETE" });
export const getDashboard = () => request(`${API_ROOT}/dashboard`);
