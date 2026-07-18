# Etapa de construcción: instala la aplicación en un entorno virtual aislado.
FROM python:3.12-slim AS constructor

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir .

# Etapa final: imagen mínima con usuario sin privilegios.
FROM python:3.12-slim

RUN useradd --create-home --shell /usr/sbin/nologin apinotas \
    && mkdir /datos \
    && chown apinotas:apinotas /datos

COPY --from=constructor /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    API_NOTAS_RUTA_BASE_DATOS=/datos/notas.db

USER apinotas
WORKDIR /app

EXPOSE 8000

CMD ["uvicorn", "api_notas.main:app", "--host", "0.0.0.0", "--port", "8000"]
