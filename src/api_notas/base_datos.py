"""Capa de acceso a datos: motor, fábrica de sesiones y base declarativa."""

from collections.abc import Iterator

from fastapi import Request
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from api_notas.config import Configuracion


class Base(DeclarativeBase):
    """Base declarativa de la que heredan todos los modelos ORM."""


def crear_motor(configuracion: Configuracion) -> Engine:
    """Crea el motor de SQLAlchemy a partir de la configuración.

    Args:
        configuracion: Ajustes con la ruta de la base de datos.

    Returns:
        Motor de SQLAlchemy listo para usarse con SQLite.
    """
    return create_engine(
        configuracion.url_base_datos,
        connect_args={"check_same_thread": False},
    )


def crear_fabrica_sesiones(motor: Engine) -> sessionmaker[Session]:
    """Crea la fábrica de sesiones ligada al motor dado.

    Args:
        motor: Motor de SQLAlchemy sobre el que se abrirán las sesiones.

    Returns:
        Fábrica de sesiones configurada para la aplicación.
    """
    return sessionmaker(bind=motor, autoflush=False, expire_on_commit=False)


def get_sesion(peticion: Request) -> Iterator[Session]:
    """Dependencia de FastAPI que entrega una sesión de base de datos.

    La fábrica de sesiones se toma del estado de la aplicación, lo que
    permite sustituir la dependencia fácilmente en los tests.

    Args:
        peticion: Petición HTTP en curso, usada para acceder a la aplicación.

    Yields:
        Sesión de SQLAlchemy que se cierra automáticamente al terminar.
    """
    fabrica: sessionmaker[Session] = peticion.app.state.fabrica_sesiones
    with fabrica() as sesion:
        yield sesion
