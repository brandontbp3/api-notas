# Registro de cambios

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y este proyecto se adhiere al [Versionado Semántico](https://semver.org/lang/es/).

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
