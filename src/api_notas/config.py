"""Configuración de la aplicación basada en variables de entorno."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    """Ajustes de la aplicación.

    Cada campo puede sobrescribirse con una variable de entorno con el
    prefijo ``API_NOTAS_``; por ejemplo, ``API_NOTAS_RUTA_BASE_DATOS``
    cambia la ubicación del archivo SQLite.
    """

    model_config = SettingsConfigDict(env_prefix="API_NOTAS_")

    ruta_base_datos: Path = Path("notas.db")
    """Ruta del archivo SQLite donde se persisten las notas."""

    nivel_registro: str = "INFO"
    """Nivel de logging de la aplicación (DEBUG, INFO, WARNING...)."""

    @property
    def url_base_datos(self) -> str:
        """URL de conexión de SQLAlchemy para la base de datos SQLite."""
        return f"sqlite:///{self.ruta_base_datos}"
