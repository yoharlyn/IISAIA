const API_ROOT = "/api";

function validationMessage(detail) {
  if (!Array.isArray(detail)) return null;
  return detail.map((item) => item.msg?.replace(/^Value error, /, "") || "Dato inválido.").join(" ");
}

async function request(path, options = {}) {
  const config = { ...options, headers: { ...(options.headers || {}) } };
  if (config.body) config.headers["Content-Type"] = "application/json";
  let response;
  try {
    response = await fetch(`${API_ROOT}${path}`, config);
  } catch {
    throw new Error("No pudimos conectar con Coffee Atlas. Revisá que el servidor esté activo.");
  }
  if (response.status === 204) return null;
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = validationMessage(data?.detail) || data?.detail;
    throw new Error(typeof detail === "string" ? detail : "La solicitud no pudo completarse.");
  }
  return data;
}

export function listCafes(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== "" && value !== null && value !== undefined) params.set(key, value);
  });
  const query = params.toString();
  return request(`/cafes${query ? `?${query}` : ""}`);
}

export const getStats = () => request("/stats");
export const createCafe = (payload) => request("/cafes", { method: "POST", body: JSON.stringify(payload) });
export const updateCafe = (id, payload) => request(`/cafes/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
export const deleteCafe = (id) => request(`/cafes/${id}`, { method: "DELETE" });

