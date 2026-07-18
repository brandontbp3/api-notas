"""Modelos ORM de la aplicación."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api_notas.base_datos import Base


def ahora_utc() -> datetime:
    """Devuelve la fecha y hora actual en UTC."""
    return datetime.now(timezone.utc)


notas_etiquetas = Table(
    "notas_etiquetas",
    Base.metadata,
    Column("nota_id", ForeignKey("notas.id"), primary_key=True),
    Column("etiqueta_id", ForeignKey("etiquetas.id"), primary_key=True),
)
"""Tabla de asociación muchos a muchos entre notas y etiquetas."""


class Nota(Base):
    """Nota personal persistida en la base de datos."""

    __tablename__ = "notas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    titulo: Mapped[str] = mapped_column(String(100))
    contenido: Mapped[str] = mapped_column(String(5000))
    creada: Mapped[datetime] = mapped_column(DateTime, default=ahora_utc)
    actualizada: Mapped[datetime] = mapped_column(DateTime, default=ahora_utc)
    etiquetas: Mapped[list["Etiqueta"]] = relationship(
        secondary=notas_etiquetas, back_populates="notas"
    )

    def __repr__(self) -> str:  # pragma: no cover
        """Representación legible de la nota para depuración."""
        return f"Nota(id={self.id!r}, titulo={self.titulo!r})"


class Etiqueta(Base):
    """Etiqueta con nombre único asociable a varias notas."""

    __tablename__ = "etiquetas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(30), unique=True)
    notas: Mapped[list[Nota]] = relationship(secondary=notas_etiquetas, back_populates="etiquetas")

    def __repr__(self) -> str:  # pragma: no cover
        """Representación legible de la etiqueta para depuración."""
        return f"Etiqueta(id={self.id!r}, nombre={self.nombre!r})"
