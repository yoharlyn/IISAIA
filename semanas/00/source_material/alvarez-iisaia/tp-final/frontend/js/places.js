export function showAutocompleteUnavailable(container, message = "Autocompletado no disponible.") {
  const fallback = document.createElement("p");
  fallback.className = "autocomplete-unavailable";
  fallback.textContent = message;
  container.replaceChildren(fallback);
}

export function mountPlaceAutocomplete(
  container,
  onSelection,
  googleObject = globalThis.google,
  { label = "Buscar una dirección en CABA", onError = null } = {},
) {
  const PlaceAutocompleteElement = googleObject?.maps?.places?.PlaceAutocompleteElement;
  if (!PlaceAutocompleteElement) {
    showAutocompleteUnavailable(container);
    return null;
  }
  const widget = new PlaceAutocompleteElement({
    includedRegionCodes: ["ar"],
    requestedLanguage: "es",
    requestedRegion: "ar",
  });
  widget.setAttribute("aria-label", label);
  widget.addEventListener("gmp-select", async (event) => {
    widget.setAttribute("aria-busy", "true");
    try {
      const place = event.placePrediction.toPlace();
      await place.fetchFields({ fields: ["id", "formattedAddress"] });
      if (!place.id) throw new Error("El resultado no tiene un Place ID verificable.");
      await onSelection({ place_id: place.id, selected_address: place.formattedAddress || "" });
    } catch (error) {
      if (onError) onError(error);
    } finally {
      widget.removeAttribute("aria-busy");
    }
  });
  container.replaceChildren(widget);
  return widget;
}
