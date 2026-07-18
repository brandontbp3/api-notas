"""Esquemas Pydantic de entrada y salida de la API."""

from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

NombreEtiqueta = Annotated[str, Field(min_length=1, max_length=30)]
"""Nombre individual de etiqueta con longitud validada (1-30 caracteres)."""


def _normalizar_etiquetas(etiquetas: list[str]) -> list[str]:
    """Pasa las etiquetas a minúsculas y elimina duplicados conservando el orden.

    Args:
        etiquetas: Nombres de etiqueta tal como los envía el cliente.

    Returns:
        Lista normalizada, en minúsculas y sin nombres repetidos.
    """
    normalizadas: list[str] = []
    for etiqueta in etiquetas:
        nombre = etiqueta.lower()
        if nombre not in normalizadas:
            normalizadas.append(nombre)
    return normalizadas


class NotaEntrada(BaseModel):
    """Datos que envía el cliente para crear o reemplazar una nota."""

    titulo: str = Field(
        min_length=1,
        max_length=100,
        description="Título de la nota",
        examples=["Lista de compras"],
    )
    contenido: str = Field(
        min_length=1,
        max_length=5000,
        description="Cuerpo de la nota",
        examples=["Pan, leche y huevos"],
    )
    etiquetas: list[NombreEtiqueta] = Field(
        default_factory=list,
        max_length=10,
        description="Etiquetas de la nota (máximo 10, en minúsculas y sin duplicados)",
        examples=[["trabajo", "ideas"]],
    )

    @field_validator("etiquetas")
    @classmethod
    def _normalizar(cls, etiquetas: list[str]) -> list[str]:
        """Normaliza las etiquetas a minúsculas y sin duplicados."""
        return _normalizar_etiquetas(etiquetas)


class NotaParcial(BaseModel):
    """Campos opcionales para la actualización parcial de una nota.

    La petición debe incluir al menos uno de los campos; los que no se
    envíen conservan su valor actual.
    """

    titulo: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Nuevo título de la nota",
        examples=["Lista de compras"],
    )
    contenido: str | None = Field(
        default=None,
        min_length=1,
        max_length=5000,
        description="Nuevo cuerpo de la nota",
        examples=["Pan, leche y huevos"],
    )
    etiquetas: list[NombreEtiqueta] | None = Field(
        default=None,
        max_length=10,
        description="Nuevas etiquetas de la nota; una lista vacía las elimina todas",
        examples=[["trabajo"]],
    )

    @field_validator("etiquetas")
    @classmethod
    def _normalizar(cls, etiquetas: list[str] | None) -> list[str] | None:
        """Normaliza las etiquetas cuando el campo está presente."""
        return None if etiquetas is None else _normalizar_etiquetas(etiquetas)

    @model_validator(mode="after")
    def _exigir_algun_campo(self) -> "NotaParcial":
        """Comprueba que la petición incluya al menos un campo a actualizar."""
        if self.titulo is None and self.contenido is None and self.etiquetas is None:
            raise ValueError("Debe enviarse al menos un campo: titulo, contenido o etiquetas")
        return self


class NotaSalida(NotaEntrada):
    """Nota completa tal como se devuelve al cliente."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Identificador único de la nota")
    creada: datetime = Field(description="Fecha de creación en UTC")
    actualizada: datetime = Field(description="Fecha de última modificación en UTC")

    @field_validator("etiquetas", mode="before")
    @classmethod
    def _extraer_nombres(cls, etiquetas: list[Any]) -> list[Any]:
        """Convierte objetos ORM ``Etiqueta`` en sus nombres al serializar."""
        return [
            etiqueta if isinstance(etiqueta, str) else etiqueta.nombre for etiqueta in etiquetas
        ]
