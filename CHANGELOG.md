# Registro de cambios

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y este proyecto se adhiere al [Versionado Semántico](https://semver.org/lang/es/).

## [1.1.0] - 2026-07-18

### Añadido

- Etiquetas opcionales en las notas (`"etiquetas": ["trabajo", "ideas"]`): máximo 10 por
  nota, cada una de 1 a 30 caracteres, normalizadas a minúsculas y sin duplicados.
- Modelo relacional muchos a muchos con SQLAlchemy 2.0: tabla `etiquetas` y tabla de
  asociación `notas_etiquetas`; las etiquetas huérfanas (sin notas) se eliminan solas.
- Filtro por etiqueta en el listado con el parámetro `etiqueta` (`GET /notas?etiqueta=trabajo`).
- Endpoint `PATCH /notas/{id}` de actualización parcial: `titulo`, `contenido` y/o
  `etiquetas` opcionales (al menos uno obligatorio); actualiza la fecha `actualizada`.
- Ordenamiento del listado con `ordenar` (`creada`, `actualizada`, `titulo`; por defecto
  `id`) y `direccion` (`asc` por defecto, `desc`), validados con 422 si el valor no es válido.
- Cabecera `X-Total-Count` en `GET /notas` con el total de resultados sin paginar,
  respetando la búsqueda y el filtro de etiqueta.

### Cambiado

- `PUT /notas/{id}` ahora reemplaza también las etiquetas de la nota (lista vacía si se omiten).

### Nota de compatibilidad

- Un `notas.db` creado con la versión 1.0.0 sigue funcionando sin migración manual: al
  arrancar, la aplicación crea automáticamente las tablas `etiquetas` y `notas_etiquetas`
  que falten, y las notas existentes se conservan y responden con `"etiquetas": []`.

## [1.0.0] - 2026-07-18

### Añadido

- CRUD completo de notas: crear, listar, obtener, actualizar y eliminar.
- Búsqueda por coincidencia en título o contenido con el parámetro `buscar`.
- Paginación con los parámetros validados `limite` y `desplazamiento`.
- Endpoint de salud `GET /salud` que responde `{"estado": "ok"}`.
- Persistencia con SQLAlchemy 2.0 sobre SQLite y creación automática de tablas.
- Configuración por variables de entorno con prefijo `API_NOTAS_` (pydantic-settings).
- Factoría de aplicación `crear_app()` con ciclo de vida y logging configurado.
- Empaquetado moderno con `pyproject.toml` (PEP 621) y layout `src/`.
- Suite de tests con pytest: CRUD, búsqueda, paginación, errores 404 y validaciones 422.
- Imagen Docker multi-stage basada en `python:3.12-slim` con usuario no root.
- Integración continua con GitHub Actions (Python 3.10 a 3.13, ruff y pytest).

### Cambiado

- Migración de sqlite3 crudo al ORM de SQLAlchemy 2.0.
- Tests migrados de unittest a pytest con fixtures y base de datos temporal.

### Eliminado

- `requirements.txt`, reemplazado por las dependencias declaradas en `pyproject.toml`.
- Módulo único `main.py` en la raíz, reemplazado por el paquete `api_notas`.
