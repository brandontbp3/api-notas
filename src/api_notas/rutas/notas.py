"""Rutas HTTP para el CRUD de notas con etiquetas, búsqueda, ordenamiento y paginación."""

import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from api_notas.base_datos import get_sesion
from api_notas.esquemas import NotaEntrada, NotaParcial, NotaSalida
from api_notas.modelos import Etiqueta, Nota, ahora_utc

registrador = logging.getLogger(__name__)

router = APIRouter(prefix="/notas", tags=["notas"])

SesionBD = Annotated[Session, Depends(get_sesion)]
"""Sesión de base de datos inyectada por FastAPI en cada petición."""

CampoOrden = Literal["id", "creada", "actualizada", "titulo"]
"""Campos por los que puede ordenarse el listado de notas."""

DireccionOrden = Literal["asc", "desc"]
"""Direcciones de ordenamiento admitidas en el listado de notas."""


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


def _obtener_o_crear_etiquetas(sesion: Session, nombres: list[str]) -> list[Etiqueta]:
    """Devuelve las etiquetas con los nombres dados, creando las que falten.

    Args:
        sesion: Sesión de base de datos activa.
        nombres: Nombres de etiqueta ya normalizados (minúsculas, sin duplicados).

    Returns:
        Etiquetas existentes o recién añadidas a la sesión, en el mismo orden.
    """
    etiquetas: list[Etiqueta] = []
    for nombre in nombres:
        etiqueta = sesion.scalar(select(Etiqueta).where(Etiqueta.nombre == nombre))
        if etiqueta is None:
            etiqueta = Etiqueta(nombre=nombre)
            sesion.add(etiqueta)
        etiquetas.append(etiqueta)
    return etiquetas


def _eliminar_etiquetas_huerfanas(sesion: Session) -> None:
    """Elimina las etiquetas que ya no están asociadas a ninguna nota.

    Vuelca los cambios pendientes de la sesión antes de buscar huérfanas
    para que las asociaciones recién quitadas se tengan en cuenta.

    Args:
        sesion: Sesión de base de datos activa, con cambios sin confirmar.
    """
    sesion.flush()
    consulta = select(Etiqueta).where(~Etiqueta.notas.any())
    for etiqueta in sesion.scalars(consulta):
        sesion.delete(etiqueta)
        registrador.info("Etiqueta huérfana %r eliminada", etiqueta.nombre)


@router.get("", response_model=list[NotaSalida], summary="Listar notas")
def listar_notas(
    sesion: SesionBD,
    respuesta: Response,
    buscar: Annotated[
        str | None, Query(description="Filtra por coincidencia en título o contenido")
    ] = None,
    etiqueta: Annotated[
        str | None, Query(description="Filtra por nombre exacto de etiqueta (sin mayúsculas)")
    ] = None,
    ordenar: Annotated[CampoOrden, Query(description="Campo por el que ordenar")] = "id",
    direccion: Annotated[DireccionOrden, Query(description="Dirección del ordenamiento")] = "asc",
    limite: Annotated[int, Query(ge=1, le=100, description="Máximo de notas a devolver")] = 50,
    desplazamiento: Annotated[int, Query(ge=0, description="Notas a omitir desde el inicio")] = 0,
) -> list[Nota]:
    """Lista notas con búsqueda, filtro por etiqueta, ordenamiento y paginación.

    La cabecera ``X-Total-Count`` de la respuesta indica el total de
    resultados sin paginar, respetando la búsqueda y el filtro de etiqueta.
    """
    consulta = select(Nota).options(selectinload(Nota.etiquetas))
    if buscar:
        patron = f"%{buscar}%"
        consulta = consulta.where(or_(Nota.titulo.like(patron), Nota.contenido.like(patron)))
    if etiqueta:
        consulta = consulta.join(Nota.etiquetas).where(Etiqueta.nombre == etiqueta.lower())
    total = sesion.scalar(select(func.count()).select_from(consulta.subquery()))
    respuesta.headers["X-Total-Count"] = str(total)
    columna = getattr(Nota, ordenar)
    consulta = consulta.order_by(columna.desc() if direccion == "desc" else columna.asc())
    consulta = consulta.offset(desplazamiento).limit(limite)
    return list(sesion.scalars(consulta).all())


@router.get("/{id_nota}", response_model=NotaSalida, summary="Obtener una nota")
def obtener_nota(id_nota: int, sesion: SesionBD) -> Nota:
    """Devuelve una nota por su id o responde 404 si no existe."""
    return _obtener_nota_o_404(sesion, id_nota)


@router.post("", response_model=NotaSalida, status_code=201, summary="Crear una nota")
def crear_nota(datos: NotaEntrada, sesion: SesionBD) -> Nota:
    """Crea una nota nueva y la devuelve con su id, fechas y etiquetas asignados."""
    nota = Nota(
        titulo=datos.titulo,
        contenido=datos.contenido,
        etiquetas=_obtener_o_crear_etiquetas(sesion, datos.etiquetas),
    )
    sesion.add(nota)
    sesion.commit()
    sesion.refresh(nota)
    registrador.info("Nota creada con id %s", nota.id)
    return nota


@router.put("/{id_nota}", response_model=NotaSalida, summary="Reemplazar una nota")
def actualizar_nota(id_nota: int, datos: NotaEntrada, sesion: SesionBD) -> Nota:
    """Reemplaza el título, el contenido y las etiquetas de una nota existente."""
    nota = _obtener_nota_o_404(sesion, id_nota)
    nota.titulo = datos.titulo
    nota.contenido = datos.contenido
    nota.etiquetas = _obtener_o_crear_etiquetas(sesion, datos.etiquetas)
    nota.actualizada = ahora_utc()
    _eliminar_etiquetas_huerfanas(sesion)
    sesion.commit()
    sesion.refresh(nota)
    registrador.info("Nota %s actualizada", id_nota)
    return nota


@router.patch("/{id_nota}", response_model=NotaSalida, summary="Actualizar parcialmente una nota")
def actualizar_nota_parcial(id_nota: int, datos: NotaParcial, sesion: SesionBD) -> Nota:
    """Actualiza solo los campos enviados de una nota existente."""
    nota = _obtener_nota_o_404(sesion, id_nota)
    if datos.titulo is not None:
        nota.titulo = datos.titulo
    if datos.contenido is not None:
        nota.contenido = datos.contenido
    if datos.etiquetas is not None:
        nota.etiquetas = _obtener_o_crear_etiquetas(sesion, datos.etiquetas)
    nota.actualizada = ahora_utc()
    _eliminar_etiquetas_huerfanas(sesion)
    sesion.commit()
    sesion.refresh(nota)
    registrador.info("Nota %s actualizada parcialmente", id_nota)
    return nota


@router.delete("/{id_nota}", status_code=204, summary="Eliminar una nota")
def eliminar_nota(id_nota: int, sesion: SesionBD) -> None:
    """Elimina una nota por su id o responde 404 si no existe."""
    nota = _obtener_nota_o_404(sesion, id_nota)
    sesion.delete(nota)
    _eliminar_etiquetas_huerfanas(sesion)
    sesion.commit()
    registrador.info("Nota %s eliminada", id_nota)
