import { apiRequest } from "./api.js";
import { currentDentist } from "./auth.js";
import { setBusy } from "./ui.js";

const form = document.querySelector("#login-form");
const username = document.querySelector("#username");
const password = document.querySelector("#password");
const toggle = document.querySelector("#toggle-password");
const submit = document.querySelector("#login-submit");
const feedback = document.querySelector("#login-feedback");

currentDentist().then(() => window.location.replace("/catalogo")).catch(() => {});

toggle.addEventListener("click", () => {
  const showing = password.type === "text";
  password.type = showing ? "password" : "text";
  toggle.textContent = showing ? "Mostrar" : "Ocultar";
  toggle.setAttribute("aria-pressed", String(!showing));
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  feedback.textContent = "";
  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }
  setBusy(submit, true, "Ingresando…");
  try {
    await apiRequest("/api/v1/auth/login", {
      method: "POST",
      body: { username: username.value, password: password.value },
    });
    feedback.textContent = "Ingreso correcto. Abriendo el catálogo…";
    window.location.replace("/catalogo");
  } catch (error) {
    feedback.textContent = error.status === 429
      ? "Demasiados intentos. Esperá unos minutos antes de volver a intentar."
      : "No pudimos iniciar sesión. Revisá tus credenciales.";
  } finally {
    setBusy(submit, false, "Ingresando…");
  }
});
