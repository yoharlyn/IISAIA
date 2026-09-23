import { apiRequest } from "./api.js";

export async function currentDentist() {
  return apiRequest("/api/v1/auth/me");
}

export async function requireDentist() {
  try {
    const user = await currentDentist();
    if (user.role !== "DENTIST") throw new Error("Invalid role");
    return user;
  } catch {
    window.location.replace("/login");
    return null;
  }
}

export async function logout() {
  await apiRequest("/api/v1/auth/logout", { method: "POST", body: {} });
  window.location.replace("/login");
}
