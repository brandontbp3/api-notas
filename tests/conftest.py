"""Fixtures compartidas para los tests de la API de notas."""

from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from api_notas.base_datos import Base, get_sesion
from api_notas.config import Configuracion
from api_notas.main import crear_app


@pytest.fixture()
def ruta_bd(tmp_path: Path) -> Path:
    """Ruta del archivo SQLite temporal usado en cada test."""
    return tmp_path / "notas_pruebas.db"


@pytest.fixture()
def fabrica_sesiones(ruta_bd: Path) -> Iterator[sessionmaker[Session]]:
    """Fábrica de sesiones sobre la base temporal, con las tablas creadas.

    Los tests pueden abrir sesiones propias con ella para inspeccionar la
    base de datos directamente (por ejemplo, las etiquetas huérfanas).
    """
    motor = create_engine(
        f"sqlite:///{ruta_bd}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=motor)
    yield sessionmaker(bind=motor, autoflush=False, expire_on_commit=False)
    motor.dispose()


@pytest.fixture()
def cliente(ruta_bd: Path, fabrica_sesiones: sessionmaker[Session]) -> Iterator[TestClient]:
    """Cliente de pruebas con una base de datos SQLite temporal.

    Sobrescribe la dependencia ``get_sesion`` para que cada petición use
    la base temporal en lugar de la real.
    """

    def get_sesion_pruebas() -> Iterator[Session]:
        with fabrica_sesiones() as sesion:
            yield sesion

    aplicacion = crear_app(Configuracion(ruta_base_datos=ruta_bd))
    aplicacion.dependency_overrides[get_sesion] = get_sesion_pruebas
    with TestClient(aplicacion) as cliente_pruebas:
        yield cliente_pruebas


@pytest.fixture()
def crear_nota(cliente: TestClient) -> Callable[..., Response]:
    """Devuelve una función auxiliar que crea notas vía POST /notas."""

    def _crear(
        titulo: str = "Mi nota",
        contenido: str = "Contenido de prueba",
        etiquetas: list[str] | None = None,
    ) -> Response:
        cuerpo: dict = {"titulo": titulo, "contenido": contenido}
        if etiquetas is not None:
            cuerpo["etiquetas"] = etiquetas
        return cliente.post("/notas", json=cuerpo)

    return _crear
