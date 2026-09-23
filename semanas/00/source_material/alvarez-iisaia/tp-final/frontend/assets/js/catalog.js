import { apiRequest } from "./api.js";
import { logout, requireDentist } from "./auth.js";
import { formatPrice, setBusy, textElement } from "./ui.js";

const grid = document.querySelector("#product-grid");
const status = document.querySelector("#catalog-status");
const form = document.querySelector("#filters-form");
const categorySelect = document.querySelector("#category");
const previous = document.querySelector("#previous-page");
const next = document.querySelector("#next-page");
const pageLabel = document.querySelector("#page-label");
const logoutButton = document.querySelector("#logout-button");
let currentPage = 1;
let totalPages = 0;

function renderProduct(product) {
  const article = document.createElement("article");
  article.className = "product-card";
  const heading = document.createElement("div");
  heading.className = "product-card-heading";
  heading.append(textElement("span", "category-tag", product.category.name));
  if (product.is_implant) heading.append(textElement("span", "implant-tag", "Implante"));
  article.append(heading, textElement("h2", "product-name", product.name));
  article.append(textElement("p", "sku", `SKU ${product.sku}`));
  article.append(textElement("p", "description", product.description || "Sin descripción"));

  const details = document.createElement("dl");
  details.className = "product-details";
  const values = [
    ["Fabricante", product.manufacturer_name],
    ["Marca", product.brand || "—"],
    ["Stock", `${product.stock} unidades`],
  ];
  if (product.implant_specs) {
    values.push(
      ["Medidas", `${product.implant_specs.diameter_mm} × ${product.implant_specs.length_mm} mm`],
      ["Conexión", product.implant_specs.connection_type || "—"],
      ["Material", product.implant_specs.material || "—"],
    );
  }
  values.forEach(([label, value]) => {
    details.append(textElement("dt", "", label), textElement("dd", "", value));
  });
  article.append(details, textElement("p", "price", formatPrice(product.price_cents)));
  return article;
}

function updateCategories(categories) {
  const selected = categorySelect.value;
  categorySelect.replaceChildren(new Option("Todas", ""));
  categories.forEach((category) => categorySelect.add(new Option(category.name, String(category.id))));
  if ([...categorySelect.options].some((option) => option.value === selected)) {
    categorySelect.value = selected;
  }
}

async function loadProducts() {
  grid.setAttribute("aria-busy", "true");
  grid.replaceChildren();
  status.textContent = "Cargando productos…";
  const data = new FormData(form);
  const params = new URLSearchParams({ page: String(currentPage), page_size: "6" });
  for (const [key, value] of data.entries()) if (value) params.set(key, value);
  try {
    const response = await apiRequest(`/api/v1/products?${params}`);
    updateCategories(response.available_categories);
    response.items.forEach((product) => grid.append(renderProduct(product)));
    totalPages = response.pagination.total_pages;
    status.textContent = response.items.length
      ? `${response.pagination.total_items} productos encontrados.`
      : "No encontramos productos para estos filtros.";
    pageLabel.textContent = totalPages ? `Página ${currentPage} de ${totalPages}` : "Sin páginas";
    previous.disabled = currentPage <= 1;
    next.disabled = currentPage >= totalPages;
  } catch (error) {
    if (error.status === 401 || error.status === 403) {
      window.location.replace("/login");
      return;
    }
    status.textContent = "No pudimos cargar el catálogo. Intentá nuevamente.";
    totalPages = 0;
    previous.disabled = true;
    next.disabled = true;
  } finally {
    grid.setAttribute("aria-busy", "false");
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  currentPage = 1;
  loadProducts();
});
previous.addEventListener("click", () => {
  if (currentPage > 1) { currentPage -= 1; loadProducts(); }
});
next.addEventListener("click", () => {
  if (currentPage < totalPages) { currentPage += 1; loadProducts(); }
});
logoutButton.addEventListener("click", async () => {
  setBusy(logoutButton, true, "Cerrando…");
  try { await logout(); } catch { status.textContent = "No pudimos cerrar la sesión."; }
  finally { setBusy(logoutButton, false, "Cerrando…"); }
});

const user = await requireDentist();
if (user) {
  document.querySelector("#user-name").textContent = `${user.first_name} ${user.last_name}`;
  await loadProducts();
}
