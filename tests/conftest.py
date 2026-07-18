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
def cliente(tmp_path: Path) -> Iterator[TestClient]:
    """Cliente de pruebas con una base de datos SQLite temporal.

    Crea un motor sobre un archivo en ``tmp_path``, genera las tablas y
    sobrescribe la dependencia ``get_sesion`` para que cada petición use
    la base temporal en lugar de la real.
    """
    ruta_bd = tmp_path / "notas_pruebas.db"
    motor = create_engine(
        f"sqlite:///{ruta_bd}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=motor)
    fabrica = sessionmaker(bind=motor, autoflush=False, expire_on_commit=False)

    def get_sesion_pruebas() -> Iterator[Session]:
        with fabrica() as sesion:
            yield sesion

    aplicacion = crear_app(Configuracion(ruta_base_datos=ruta_bd))
    aplicacion.dependency_overrides[get_sesion] = get_sesion_pruebas
    with TestClient(aplicacion) as cliente_pruebas:
        yield cliente_pruebas
    motor.dispose()


@pytest.fixture()
def crear_nota(cliente: TestClient) -> Callable[..., Response]:
    """Devuelve una función auxiliar que crea notas vía POST /notas."""

    def _crear(titulo: str = "Mi nota", contenido: str = "Contenido de prueba") -> Response:
        return cliente.post("/notas", json={"titulo": titulo, "contenido": contenido})

    return _crear
