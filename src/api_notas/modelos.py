"""Modelos ORM de la aplicación."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from api_notas.base_datos import Base


def ahora_utc() -> datetime:
    """Devuelve la fecha y hora actual en UTC."""
    return datetime.now(timezone.utc)


class Nota(Base):
    """Nota personal persistida en la base de datos."""

    __tablename__ = "notas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    titulo: Mapped[str] = mapped_column(String(100))
    contenido: Mapped[str] = mapped_column(String(5000))
    creada: Mapped[datetime] = mapped_column(DateTime, default=ahora_utc)
    actualizada: Mapped[datetime] = mapped_column(DateTime, default=ahora_utc)

    def __repr__(self) -> str:  # pragma: no cover
        """Representación legible de la nota para depuración."""
        return f"Nota(id={self.id!r}, titulo={self.titulo!r})"
