"""Esquemas Pydantic de entrada y salida de la API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotaEntrada(BaseModel):
    """Datos que envía el cliente para crear o actualizar una nota."""

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


class NotaSalida(NotaEntrada):
    """Nota completa tal como se devuelve al cliente."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Identificador único de la nota")
    creada: datetime = Field(description="Fecha de creación en UTC")
    actualizada: datetime = Field(description="Fecha de última modificación en UTC")
