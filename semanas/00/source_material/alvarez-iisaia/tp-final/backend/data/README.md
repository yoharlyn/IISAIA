# Datos geográficos de CABA

Coffee Atlas incluye dos recursos oficiales de Buenos Aires Data, Gobierno de la
Ciudad Autónoma de Buenos Aires, bajo licencia `CC-BY-2.5-AR`:

- `caba_perimeter.geojson`: dataset **Perímetro**, recurso “Perímetro
  (GeoJSON)”. Fuente:
  <https://cdn.buenosaires.gob.ar/datosabiertos/datasets/perimetro/perimetro.geojson>
- `caba_neighborhoods.geojson`: dataset **Barrios**, recurso “Barrios
  (GeoJSON)”. Fuente:
  <https://cdn.buenosaires.gob.ar/datosabiertos/datasets/barrios/barrios.geojson>

Descargados el 14 de octubre de 2026. Los catálogos oficiales informaban fecha
de actualización 29 de julio de 2026 y frecuencia trimestral. La constante
`CABA_POLYGON_VERSION` identifica esa revisión para la evidencia local de
validación.

Los archivos se conservan sin simplificar. El perímetro decide pertenencia a
CABA y los polígonos de barrios permiten derivar el barrio sin persistir los
componentes de dirección de Google.
