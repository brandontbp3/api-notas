"""Punto de entrada y factoría de la aplicación FastAPI."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api_notas import __version__
from api_notas.base_datos import Base, crear_fabrica_sesiones, crear_motor
from api_notas.config import Configuracion
from api_notas.rutas.notas import router as router_notas

registrador = logging.getLogger(__name__)


def configurar_registro(nivel: str) -> None:
    """Configura el logging global de la aplicación.

    Args:
        nivel: Nivel de logging, por ejemplo ``"INFO"`` o ``"DEBUG"``.
    """
    logging.basicConfig(
        level=nivel.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def crear_app(configuracion: Configuracion | None = None) -> FastAPI:
    """Factoría de la aplicación FastAPI.

    Args:
        configuracion: Ajustes a usar; si es ``None`` se leen del entorno.

    Returns:
        Aplicación configurada con sus rutas, estado y ciclo de vida.
    """
    ajustes = configuracion if configuracion is not None else Configuracion()
    configurar_registro(ajustes.nivel_registro)
    motor = crear_motor(ajustes)

    @asynccontextmanager
    async def ciclo_vida(app: FastAPI) -> AsyncIterator[None]:
        """Crea las tablas al arrancar y libera el motor al terminar."""
        Base.metadata.create_all(bind=motor)
        registrador.info("Base de datos lista en %s", ajustes.ruta_base_datos)
        yield
        motor.dispose()

    aplicacion = FastAPI(
        title="API de Notas",
        description="API REST para gestionar notas personales",
        version=__version__,
        lifespan=ciclo_vida,
    )
    aplicacion.state.configuracion = ajustes
    aplicacion.state.fabrica_sesiones = crear_fabrica_sesiones(motor)
    aplicacion.include_router(router_notas)

    @aplicacion.get("/salud", tags=["salud"], summary="Estado del servicio")
    def salud() -> dict[str, str]:
        """Comprueba que el servicio está operativo."""
        return {"estado": "ok"}

    return aplicacion


app = crear_app()
"""Instancia de la aplicación usada por uvicorn (``api_notas.main:app``)."""
