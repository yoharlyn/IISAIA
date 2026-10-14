import { ApiError, getSession, logoutSession, setCsrfToken } from "./api.js";

const loading = document.querySelector("#session-loading");
const loginView = document.querySelector("#login-view");
const authenticated = document.querySelectorAll(".authenticated-content");
const sessionName = document.querySelector("#session-name");
const sessionEmail = document.querySelector("#session-email");
const logoutButton = document.querySelector("#logout-button");

function showLogin(message = "Iniciá sesión para abrir tu atlas personal.") {
  setCsrfToken(null);
  loading.hidden = true;
  authenticated.forEach((element) => { element.hidden = true; });
  loginView.hidden = false;
  document.querySelector("#login-message").textContent = message;
  document.querySelector("#login-link").focus();
}

function showApplication(session) {
  setCsrfToken(session.csrf_token);
  sessionName.textContent = session.user.display_name;
  sessionEmail.textContent = session.user.email || "Identidad administrada por Auth0";
  loading.hidden = true;
  loginView.hidden = true;
  authenticated.forEach((element) => { element.hidden = false; });
}

export async function initializeSession(onAuthenticated) {
  loading.hidden = false;
  try {
    const session = await getSession();
    showApplication(session);
    await onAuthenticated(session);
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      showLogin();
      return;
    }
    showLogin("No pudimos comprobar tu sesión. Intentá nuevamente.");
  }
}

window.addEventListener("coffee-atlas:session-expired", () => {
  showLogin("Tu sesión venció. Iniciá sesión nuevamente para continuar.");
});

logoutButton.addEventListener("click", async () => {
  logoutButton.disabled = true;
  logoutButton.textContent = "Cerrando sesión…";
  try {
    const result = await logoutSession();
    setCsrfToken(null);
    window.location.assign(result.logout_url || "/");
  } catch (error) {
    if (!(error instanceof ApiError && error.status === 401)) {
      document.querySelector("#global-message").textContent = error.message;
    }
    showLogin("La sesión local terminó. Es posible que la sesión de Auth0 siga activa.");
  } finally {
    logoutButton.disabled = false;
    logoutButton.textContent = "Cerrar sesión";
  }
});
