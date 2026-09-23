export class ApiError extends Error {
  constructor(status, payload) {
    super(payload?.error?.message || "No se pudo completar la solicitud.");
    this.name = "ApiError";
    this.status = status;
    this.code = payload?.error?.code || "UNKNOWN_ERROR";
  }
}

export async function apiRequest(path, options = {}) {
  const requestOptions = {
    method: options.method || "GET",
    credentials: "same-origin",
    headers: { Accept: "application/json", ...(options.headers || {}) },
  };
  if (options.body !== undefined) {
    requestOptions.body = JSON.stringify(options.body);
    requestOptions.headers["Content-Type"] = "application/json";
    requestOptions.headers["X-CSRF-Protection"] = "1";
  }
  const response = await fetch(path, requestOptions);
  if (!response.ok) {
    let payload;
    try {
      payload = await response.json();
    } catch {
      payload = null;
    }
    throw new ApiError(response.status, payload);
  }
  return response.status === 204 ? null : response.json();
}
