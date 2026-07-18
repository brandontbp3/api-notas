"""Rutas HTTP para el CRUD de notas con búsqueda y paginación."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from api_notas.base_datos import get_sesion
from api_notas.esquemas import NotaEntrada, NotaSalida
from api_notas.modelos import Nota, ahora_utc

registrador = logging.getLogger(__name__)

router = APIRouter(prefix="/notas", tags=["notas"])

SesionBD = Annotated[Session, Depends(get_sesion)]
"""Sesión de base de datos inyectada por FastAPI en cada petición."""


def _obtener_nota_o_404(sesion: Session, id_nota: int) -> Nota:
    """Devuelve la nota con el id dado o lanza un error HTTP 404.

    Args:
        sesion: Sesión de base de datos activa.
        id_nota: Identificador de la nota buscada.

    Returns:
        La nota encontrada.

    Raises:
        HTTPException: Con código 404 si la nota no existe.
    """
    nota = sesion.get(Nota, id_nota)
    if nota is None:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    return nota


@router.get("", response_model=list[NotaSalida], summary="Listar notas")
def listar_notas(
    sesion: SesionBD,
    buscar: Annotated[
        str | None, Query(description="Filtra por coincidencia en título o contenido")
    ] = None,
    limite: Annotated[int, Query(ge=1, le=100, description="Máximo de notas a devolver")] = 50,
    desplazamiento: Annotated[int, Query(ge=0, description="Notas a omitir desde el inicio")] = 0,
) -> list[Nota]:
    """Lista las notas ordenadas por id, con búsqueda y paginación opcionales."""
    consulta = select(Nota).order_by(Nota.id)
    if buscar:
        patron = f"%{buscar}%"
        consulta = consulta.where(or_(Nota.titulo.like(patron), Nota.contenido.like(patron)))
    consulta = consulta.offset(desplazamiento).limit(limite)
    return list(sesion.scalars(consulta).all())


@router.get("/{id_nota}", response_model=NotaSalida, summary="Obtener una nota")
def obtener_nota(id_nota: int, sesion: SesionBD) -> Nota:
    """Devuelve una nota por su id o responde 404 si no existe."""
    return _obtener_nota_o_404(sesion, id_nota)


@router.post("", response_model=NotaSalida, status_code=201, summary="Crear una nota")
def crear_nota(datos: NotaEntrada, sesion: SesionBD) -> Nota:
    """Crea una nota nueva y la devuelve con su id y fechas asignados."""
    nota = Nota(titulo=datos.titulo, contenido=datos.contenido)
    sesion.add(nota)
    sesion.commit()
    sesion.refresh(nota)
    registrador.info("Nota creada con id %s", nota.id)
    return nota


@router.put("/{id_nota}", response_model=NotaSalida, summary="Actualizar una nota")
def actualizar_nota(id_nota: int, datos: NotaEntrada, sesion: SesionBD) -> Nota:
    """Actualiza el título y el contenido de una nota existente."""
    nota = _obtener_nota_o_404(sesion, id_nota)
    nota.titulo = datos.titulo
    nota.contenido = datos.contenido
    nota.actualizada = ahora_utc()
    sesion.commit()
    sesion.refresh(nota)
    registrador.info("Nota %s actualizada", id_nota)
    return nota


@router.delete("/{id_nota}", status_code=204, summary="Eliminar una nota")
def eliminar_nota(id_nota: int, sesion: SesionBD) -> None:
    """Elimina una nota por su id o responde 404 si no existe."""
    nota = _obtener_nota_o_404(sesion, id_nota)
    sesion.delete(nota)
    sesion.commit()
    registrador.info("Nota %s eliminada", id_nota)
