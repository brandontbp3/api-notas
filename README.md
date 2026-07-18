# API de Notas

[![CI](https://github.com/brandontbp3/api-notas/actions/workflows/ci.yml/badge.svg)](https://github.com/brandontbp3/api-notas/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Licencia MIT](https://img.shields.io/badge/licencia-MIT-green.svg)](LICENSE)
[![Tests: pytest](https://img.shields.io/badge/tests-pytest-0A9EDC.svg)](https://docs.pytest.org/)
[![Linter: ruff](https://img.shields.io/badge/linter-ruff-261230.svg)](https://docs.astral.sh/ruff/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-d71f00.svg)](https://www.sqlalchemy.org/)

API REST para gestionar notas personales, construida con **FastAPI** y **SQLAlchemy 2.0**
sobre **SQLite**. Incluye CRUD completo, etiquetas, búsqueda, ordenamiento, paginación,
validación con Pydantic, imagen Docker lista para producción y suite de tests con pytest.

## Características

- CRUD completo de notas con fechas de creación y actualización automáticas.
- Actualización parcial con `PATCH /notas/{id}` (`titulo`, `contenido` y/o `etiquetas`).
- Etiquetas por nota (máximo 10, de 1 a 30 caracteres, en minúsculas y sin duplicados)
  con modelo muchos a muchos; las etiquetas sin notas se eliminan automáticamente.
- Búsqueda por coincidencia en título o contenido (`?buscar=`) y filtro por
  etiqueta (`?etiqueta=`).
- Ordenamiento con `?ordenar=` (`creada`, `actualizada`, `titulo`; por defecto `id`)
  y `?direccion=` (`asc` o `desc`).
- Paginación validada con `limite` (1-100) y `desplazamiento` (>= 0), y cabecera
  `X-Total-Count` con el total de resultados sin paginar.
- Endpoint de salud `GET /salud` para monitorización.
- Configuración por variables de entorno con prefijo `API_NOTAS_`.
- Documentación interactiva automática (Swagger UI) en `/docs`.
- Empaquetado moderno (PEP 621, layout `src/`) y Docker multi-stage sin root.

## Instalación

Requiere Python 3.10 o superior.

```bash
# Crear y activar un entorno virtual
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS

# Instalar el paquete
pip install -e .
```

## Configuración

Todas las variables de entorno usan el prefijo `API_NOTAS_`:

| Variable                     | Descripción                              | Valor por defecto |
|------------------------------|------------------------------------------|-------------------|
| `API_NOTAS_RUTA_BASE_DATOS`  | Ruta del archivo SQLite de la aplicación | `notas.db`        |
| `API_NOTAS_NIVEL_REGISTRO`   | Nivel de logging (`DEBUG`, `INFO`...)    | `INFO`            |

Ejemplo:

```bash
# Windows (PowerShell)
$env:API_NOTAS_RUTA_BASE_DATOS = "C:\datos\notas.db"

# Linux / macOS
export API_NOTAS_RUTA_BASE_DATOS=/datos/notas.db
```

## Uso

### Con uvicorn

```bash
uvicorn api_notas.main:app --reload
```

La API queda disponible en `http://127.0.0.1:8000` y la documentación interactiva
en `http://127.0.0.1:8000/docs`.

### Con Docker

```bash
# Construir la imagen
docker build -t api-notas .

# Ejecutar el contenedor (la base de datos vive en /datos dentro del contenedor)
docker run --rm -p 8000:8000 -v notas_datos:/datos api-notas
```

## Endpoints

| Método | Ruta            | Descripción                                                                          |
|--------|-----------------|--------------------------------------------------------------------------------------|
| GET    | `/salud`        | Estado del servicio: `{"estado": "ok"}`                                              |
| GET    | `/notas`        | Listar notas (`?buscar=`, `?etiqueta=`, `?ordenar=`, `?direccion=`, `?limite=`, `?desplazamiento=`) |
| GET    | `/notas/{id}`   | Obtener una nota por su id                                                           |
| POST   | `/notas`        | Crear una nota, con etiquetas opcionales (responde `201`)                            |
| PUT    | `/notas/{id}`   | Reemplazar el título, el contenido y las etiquetas de una nota                       |
| PATCH  | `/notas/{id}`   | Actualizar solo los campos enviados (al menos uno obligatorio)                       |
| DELETE | `/notas/{id}`   | Eliminar una nota (responde `204`)                                                   |

Las notas inexistentes responden `404` y los datos inválidos `422`.

### Etiquetas

Las notas aceptan una lista opcional `etiquetas` de hasta 10 nombres de 1 a 30
caracteres. Se normalizan a minúsculas y se descartan los duplicados; las
etiquetas que se quedan sin notas se eliminan automáticamente de la base de datos.

### Ordenamiento y total de resultados

`GET /notas` admite `ordenar` (`creada`, `actualizada` o `titulo`; por defecto
ordena por `id`) y `direccion` (`asc` por defecto, `desc`); un valor no válido
responde `422`. Ambos se combinan con búsqueda, filtro de etiqueta y paginación.
La respuesta incluye la cabecera `X-Total-Count` con el total de resultados sin
paginar (respetando `buscar` y `etiqueta`), útil para calcular páginas.

### Ejemplos con curl

```bash
# Crear una nota con etiquetas
curl -X POST http://127.0.0.1:8000/notas \
  -H "Content-Type: application/json" \
  -d '{"titulo": "Mi primera nota", "contenido": "Hola mundo", "etiquetas": ["trabajo", "ideas"]}'

# Listar con búsqueda y paginación
curl "http://127.0.0.1:8000/notas?buscar=nota&limite=10&desplazamiento=0"

# Filtrar por etiqueta y ordenar por fecha de creación descendente
curl "http://127.0.0.1:8000/notas?etiqueta=trabajo&ordenar=creada&direccion=desc"

# Ver la cabecera X-Total-Count con el total sin paginar
curl -i "http://127.0.0.1:8000/notas?limite=1"

# Reemplazar la nota 1 (PUT también reemplaza las etiquetas)
curl -X PUT http://127.0.0.1:8000/notas/1 \
  -H "Content-Type: application/json" \
  -d '{"titulo": "Editada", "contenido": "Contenido nuevo", "etiquetas": ["personal"]}'

# Actualizar solo el título de la nota 1
curl -X PATCH http://127.0.0.1:8000/notas/1 \
  -H "Content-Type: application/json" \
  -d '{"titulo": "Solo cambio el título"}'

# Quitar todas las etiquetas de la nota 1
curl -X PATCH http://127.0.0.1:8000/notas/1 \
  -H "Content-Type: application/json" \
  -d '{"etiquetas": []}'

# Eliminar la nota 1
curl -X DELETE http://127.0.0.1:8000/notas/1
```

> **Compatibilidad**: un `notas.db` creado con la versión 1.0.0 funciona sin cambios:
> al arrancar, la 1.1.0 crea automáticamente las tablas de etiquetas que falten y las
> notas existentes se conservan y responden con `"etiquetas": []`.

## Desarrollo

```bash
# Instalar dependencias de desarrollo
pip install -e ".[dev]"

# Ejecutar los tests (usan una base de datos temporal)
pytest

# Lint y formato
ruff check .
ruff format --check .
```

## Estructura del proyecto

```
api-notas/
├── src/
│   └── api_notas/
│       ├── __init__.py        # Versión del paquete
│       ├── config.py          # Configuración (pydantic-settings)
│       ├── base_datos.py      # Motor, sesiones y base declarativa
│       ├── modelos.py         # Modelos ORM Nota y Etiqueta (muchos a muchos)
│       ├── esquemas.py        # Esquemas Pydantic de entrada/salida
│       ├── main.py            # Factoría crear_app() y endpoint /salud
│       └── rutas/
│           └── notas.py       # CRUD, etiquetas, búsqueda, ordenamiento y paginación
├── tests/
│   ├── conftest.py            # Fixtures (BD temporal, TestClient)
│   └── test_api.py            # Tests de la API
├── .github/workflows/ci.yml   # Integración continua
├── Dockerfile                 # Imagen multi-stage sin root
├── pyproject.toml             # Metadatos, dependencias y ruff
├── CHANGELOG.md
├── LICENSE
└── README.md
```

## Licencia

Este proyecto se distribuye bajo la licencia [MIT](LICENSE).
