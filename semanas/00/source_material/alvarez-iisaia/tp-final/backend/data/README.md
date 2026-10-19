# Datos geográficos de CABA

Coffee Atlas incluye dos recursos oficiales de Buenos Aires Data, Gobierno de la
Ciudad Autónoma de Buenos Aires, bajo licencia `CC-BY-2.5-AR`:

- `caba_perimeter.geojson`: dataset **Perímetro**, recurso “Perímetro
  (GeoJSON)”. Fuente:
  <https://cdn.buenosaires.gob.ar/datosabiertos/datasets/perimetro/perimetro.geojson>
- `caba_neighborhoods.geojson`: dataset **Barrios**, recurso “Barrios
  (GeoJSON)”. Fuente:
  <https://cdn.buenosaires.gob.ar/datosabiertos/datasets/barrios/barrios.geojson>

Incorporados al repositorio el 14 de octubre de 2026. La versión local del
catálogo de barrios se identifica además por el SHA-256
`272119879eaa382a99008273e67b033d2c9f01241db823088e04cfe9a720a69b`.
La constante `CABA_POLYGON_VERSION` conserva el identificador de revisión usado
por la evidencia local de validación.

Los archivos se conservan sin simplificar. El perímetro decide pertenencia a
CABA y los polígonos de barrios permiten derivar el barrio sin persistir los
componentes de dirección de Google.
