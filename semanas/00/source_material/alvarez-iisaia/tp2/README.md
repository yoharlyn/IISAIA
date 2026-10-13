# TP 2 — API de música y playlists

Un archivo `openapi.yaml` que describe el contrato de una API REST para administrar usuarios, artistas, álbumes, canciones y playlists. El contrato contiene 5 recursos y 13 operaciones distribuidas en 8 paths. No incluye una implementación: el entregable es la especificación de la API en OpenAPI 3.1.0.

## Cómo visualizar la API

Pegar el contenido de [openapi.yaml](openapi.yaml) en [Swagger Editor](https://editor.swagger.io). La documentación navegable aparecerá en el panel derecho, con los endpoints agrupados por recurso y la posibilidad de revisar sus parámetros, bodies, respuestas y ejemplos.

## Qué me propuse construir

Busqué modelar una plataforma de música con recursos que tuvieran relaciones claras entre sí. Un artista publica álbumes, cada álbum contiene canciones, los usuarios crean playlists y las playlists agrupan canciones existentes.

La API permite listar y crear artistas, álbumes, canciones, usuarios y playlists. También permite consultar una playlist con sus canciones, agregar una canción a una playlist y eliminarla. Para cada operación se documentan los códigos de respuesta exitosos y los posibles errores.

El contrato se generó mediante dos prompts realizados en una sola conversación con la IA. El primer prompt definió el dominio y los endpoints, el segundo corrigió y completó aspectos detectados durante la revisión del resultado inicial.

## Decisiones de diseño

**Paths anidados para representar pertenencia.** Los álbumes se administran dentro de `/artists/{artistId}/albums` y las canciones dentro de `/albums/{albumId}/songs`. La URL identifica el recurso padre y evita tener que volver a enviar `artist_id` o `album_id` en el body. De la misma manera, las playlists se crean dentro de `/users/{userId}/playlists`, por lo que `user_id` se obtiene del path.

**Schemas de entrada y salida separados.** Los schemas de entrada, como `ArtistInput`, `AlbumInput`, `SongInput` y `PlaylistInput`, contienen solamente los datos que debe proporcionar el cliente. Los schemas de salida incluyen además el `id` generado por el servidor y las referencias que se deducen del path. Esto diferencia con claridad lo que el cliente envía de lo que recibe como respuesta.

**UUID para los identificadores.** Todos los identificadores están definidos como strings con formato `uuid`. Los ejemplos utilizan UUID coherentes entre sí para que las relaciones entre artistas, álbumes, canciones, usuarios y playlists puedan seguirse fácilmente.

**Una playlist devuelve objetos `Song`.** Tanto el detalle de una playlist como el listado de playlists de un usuario incluyen el array `songs` con los objetos completos. Para este contrato prioricé que la respuesta mostrara toda la relación entre los recursos.

**Agregar una canción devuelve `201 Created`.** La canción y la playlist ya existen, pero la operación crea una nueva asociación entre ambas. Por esa razón, `POST /playlists/{playlistId}/songs` responde con `201` y devuelve la playlist actualizada.

**`204 No Content` al eliminar una canción de una playlist.** Cuando la asociación se elimina correctamente, el endpoint no devuelve un body. Si la playlist o la canción no existen, o si la canción no pertenece a la playlist, devuelve `404` con un error específico.

**Errores con una estructura común y causas específicas.** Todas las respuestas de error utilizan el schema reutilizable `Error`, compuesto por `code`, `message` y `details`. Cada endpoint proporciona códigos y ejemplos adecuados para su contexto, como `ARTIST_NOT_FOUND`, `VALIDATION_ERROR`, `EMAIL_ALREADY_EXISTS` o `SONG_ALREADY_IN_PLAYLIST`.

**Validaciones de los datos.** Los campos obligatorios están declarados mediante `required`. Los textos requeridos tienen una longitud mínima, los correos electrónicos utilizan el formato `email`, `release_date` utiliza el formato `date` y `duration_seconds` debe ser un entero mayor que cero. La fecha de publicación de un álbum es opcional.

## Qué corregí después de la primera iteración

La primera respuesta de la IA fue más completa de lo solicitado: además de generar los endpoints, infirió UUID, formatos, validaciones, componentes reutilizables, parámetros de ruta, tags, `operationId` y un schema común de error. Sin embargo, al revisar el archivo encontré cuatro aspectos que necesitaban ajustes.

El servidor estaba definido como `https://api.example.com`, por lo que lo reemplacé por una URL local ficticia de desarrollo. Los ejemplos existentes correspondían principalmente a propiedades individuales y no mostraban bodies completos de solicitudes y respuestas. Las respuestas de error compartían descripciones demasiado generales, sin distinguir con precisión qué recurso no existía o qué validación había fallado. Finalmente, el listado de playlists utilizaba `PlaylistSummary`, un schema que no incluía sus canciones.

En el segundo prompt pedí corregir específicamente esos puntos. El resultado incorporó ejemplos completos y relacionados entre sí, errores contextualizados que conservan el schema común `Error` y el uso de `Playlist` en el listado del usuario. Como `PlaylistSummary` dejó de ser necesario, también fue eliminado.

La principal conclusión del proceso fue que una primera respuesta técnicamente válida todavía necesita revisión. La iteración no se limitó a corregir sintaxis: permitió hacer explícitas decisiones del contrato que la IA había tomado por su cuenta o había dejado definidas de manera demasiado general.

## Prompts

El registro de las dos iteraciones, junto con sus objetivos y resultados, está disponible en [prompts.md](prompts.md).
