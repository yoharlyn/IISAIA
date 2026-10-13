# Prompts — TP 2

Registro del proceso de generación del contrato OpenAPI para una plataforma de música y playlists. Se realizaron dos iteraciones en una sola conversación y el archivo `openapi.yaml` quedó terminado en la segunda.

---

## 1 — Prompt inicial

```text
Necesito que generes un archivo openapi.yaml válido, utilizando OpenAPI 3.1.0, para una API REST de una plataforma de música y playlists.

Recursos:

  User {
    id,
    username,
    email
  }

  Artist {
    id,
    name
  }

  Album {
    id,
    title,
    release_date?,
    artist_id
  }

  Song {
    id,
    title,
    duration_seconds,
    album_id
  }

  Playlist {
    id,
    name,
    user_id,
    songs[]
  }

Los campos marcados con “?” son opcionales.

Endpoints:

  GET    /artists
    → 200 lista de artistas

  POST   /artists
    → 201 artista creado
    → 400 si falta name o el valor es inválido

  GET    /artists/{artistId}/albums
    → 200 lista de álbumes del artista
    → 404 si el artista no existe

  POST   /artists/{artistId}/albums
    → 201 álbum creado
    → 400 si falta title o algún dato es inválido
    → 404 si el artista no existe

  GET    /albums/{albumId}/songs
    → 200 lista de canciones del álbum
    → 404 si el álbum no existe

  POST   /albums/{albumId}/songs
    → 201 canción creada
    → 400 si falta title, falta duration_seconds o la duración no es válida
    → 404 si el álbum no existe

  GET    /users
    → 200 lista de usuarios

  POST   /users
    → 201 usuario creado
    → 400 si falta username, falta email o el email no tiene un formato válido
    → 409 si ya existe un usuario con el mismo email

  GET    /users/{userId}/playlists
    → 200 lista de playlists del usuario
    → 404 si el usuario no existe

  POST   /users/{userId}/playlists
    → 201 playlist creada
    → 400 si falta name
    → 404 si el usuario no existe

  GET    /playlists/{playlistId}
    → 200 detalle de la playlist, incluyendo sus canciones
    → 404 si la playlist no existe

  POST   /playlists/{playlistId}/songs
    Body: { song_id }
    → 201 canción agregada a la playlist
    → 400 si falta song_id
    → 404 si la playlist o la canción no existen
    → 409 si la canción ya pertenece a la playlist

  DELETE /playlists/{playlistId}/songs/{songId}
    → 204 canción eliminada de la playlist
    → 404 si la playlist no existe, la canción no existe o la canción no pertenece a la playlist

Requisitos adicionales:

- Los schemas de entrada y salida deben ser diferentes.
- Los schemas de entrada no deben incluir los identificadores generados por el servidor.
- La respuesta de detalle de una playlist debe incluir un array de objetos Song.
```

**Objetivos:** definir los recursos de la plataforma, sus relaciones y los endpoints básicos, incluyendo los códigos de respuesta esperados. También quería separar los schemas de entrada y salida para que los identificadores generados por el servidor no fueran enviados por el cliente.

**Resultado:** La IA generó un contrato OpenAPI 3.1.0 completo con los endpoints solicitados. Además, infirió varias convenciones que no estaban expresadas en el prompt: identificadores UUID, formatos para fechas y correos electrónicos, validaciones, componentes reutilizables, parámetros de ruta, `operationId`, etiquetas y un schema común para los errores. Al revisar el resultado encontré aspectos para precisar: utilizaba un servidor de ejemplo, solo incluía ejemplos de propiedades individuales, las respuestas de error eran genéricas y el listado de playlists devolvía un schema resumido sin sus canciones.

---

## 2 — Corregir y completar la especificación

```text
Modifica el archivo openapi.yaml generado anteriormente para corregir únicamente
los siguientes aspectos:

1. Servidor local

Reemplaza el servidor https://api.example.com por:

http://localhost:8080/api/v1

Indica que se trata del servidor local de desarrollo.

2. Ejemplos completos

Actualmente existen ejemplos para algunas propiedades individuales, pero no para
el body completo de cada enpoint.

Agrega ejemplos completos y realistas para:

- los request body de todos los endpoints POST
- las respuestas exitosas
- las respuestas que devuelven listas
- las respuestas de error 400, 404 y 409

Los ejemplos deben ser coherentes entre sí. Utiliza UUID válidos y conserva los
ejemplos relacionados con la plataforma de música.

La respuesta 204 del endpoint DELETE no debe incluir body ni ejemplo.

3. Respuestas de error específicas

Conserva el schema reutilizable Error con los campos code, message y details,
pero evita que las respuestas de error sean excesivamente genéricas.

Cada operación debe indicar claramente la causa del error. Por ejemplo:

- ARTIST_NOT_FOUND si no existe el artista
- ALBUM_NOT_FOUND si no existe el álbum
- USER_NOT_FOUND si no existe el usuario
- PLAYLIST_NOT_FOUND si no existe la playlist
- SONG_NOT_FOUND si no existe la canción
- VALIDATION_ERROR si los datos enviados son inválidos
- EMAIL_ALREADY_EXISTS si el email ya está registrado
- SONG_ALREADY_IN_PLAYLIST si la canción ya pertenece a la playlist

Cuando un mismo código HTTP pueda representar más de una causa, incluye ejemplos
que documenten las distintas posibilidades.

El schema Error debe seguir siendo reutilizable, no dupliques su estructura en
cada endpoint.

4. Listado de playlists

Actualmente GET /users/{userId}/playlists devuelve objetos PlaylistSummary sin
el array songs.

Modifica ese endpoint para que la respuesta 200 utilice el schema Playlist y,
por lo tanto, cada playlist del listado incluya:

- id
- name
- user_id
- songs como un array de objetos Song

Elimina el schema PlaylistSummary si deja de utilizarse en el documento.
```

**Objetivos:** corregir aspectos concretos detectados al revisar la primera respuesta. Quería utilizar una URL local ficticia del posible proyecto, documentar el body completo de cada endpoint mediante ejemplos coherentes, distinguir las diferentes causas de error sin duplicar el schema `Error` y hacer que el listado de playlists devolviera el recurso completo con sus canciones.

**Resultado:** La IA reemplazó el servidor por `http://localhost:8080/api/v1`, agregó ejemplos completos para solicitudes, respuestas exitosas, listas y errores, y mantuvo la respuesta `204` sin cuerpo. También especializó los errores mediante códigos y mensajes adecuados para cada situación, pero conservó un único schema reutilizable. Finalmente, cambió el listado para utilizar `Playlist`, incluyó el array de objetos `Song` y eliminó `PlaylistSummary`. El resultado mantuvo los endpoints y códigos HTTP definidos inicialmente, incluido `201 Created` al crear la asociación entre una canción y una playlist.

---

## Conversación completa

Los dos prompts se realizaron en una sola conversación, sin reiniciar el contexto. El contrato final contiene 5 recursos y 13 operaciones distribuidas en 8 paths.
