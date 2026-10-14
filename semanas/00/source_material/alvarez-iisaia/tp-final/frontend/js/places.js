export function showAutocompleteUnavailable(container, message = "Autocompletado no disponible.") {
  const fallback = document.createElement("p");
  fallback.className = "autocomplete-unavailable";
  fallback.textContent = message;
  container.replaceChildren(fallback);
}

export function mountPlaceAutocomplete(container, onSelection, googleObject = globalThis.google) {
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
  widget.setAttribute("aria-label", "Buscar una dirección en CABA");
  widget.addEventListener("gmp-select", async (event) => {
    const place = event.placePrediction.toPlace();
    await place.fetchFields({ fields: ["id", "formattedAddress"] });
    if (place.id && place.formattedAddress) {
      onSelection({ place_id: place.id, selected_address: place.formattedAddress });
    }
  });
  container.replaceChildren(widget);
  return widget;
}
