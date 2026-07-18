"""Tests de la API de notas: CRUD, búsqueda, paginación y validaciones."""

from collections.abc import Callable
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response

CrearNota = Callable[..., Response]


def test_salud(cliente: TestClient) -> None:
    respuesta = cliente.get("/salud")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok"}


# ---------------------------------------------------------------- creación


def test_crear_nota(crear_nota: CrearNota) -> None:
    respuesta = crear_nota("Mi nota", "Contenido de prueba")
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["id"] == 1
    assert datos["titulo"] == "Mi nota"
    assert datos["contenido"] == "Contenido de prueba"


def test_crear_nota_incluye_fechas(crear_nota: CrearNota) -> None:
    datos = crear_nota().json()
    creada = datetime.fromisoformat(datos["creada"])
    actualizada = datetime.fromisoformat(datos["actualizada"])
    assert actualizada >= creada


def test_crear_notas_asigna_ids_consecutivos(crear_nota: CrearNota) -> None:
    assert crear_nota("Primera").json()["id"] == 1
    assert crear_nota("Segunda").json()["id"] == 2


# ----------------------------------------------------------------- lectura


def test_listar_sin_notas_devuelve_lista_vacia(cliente: TestClient) -> None:
    respuesta = cliente.get("/notas")
    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_listar_notas_ordenadas_por_id(cliente: TestClient, crear_nota: CrearNota) -> None:
    crear_nota("Nota A")
    crear_nota("Nota B")
    titulos = [nota["titulo"] for nota in cliente.get("/notas").json()]
    assert titulos == ["Nota A", "Nota B"]


def test_obtener_nota(cliente: TestClient, crear_nota: CrearNota) -> None:
    crear_nota("Única", "Texto")
    respuesta = cliente.get("/notas/1")
    assert respuesta.status_code == 200
    assert respuesta.json()["titulo"] == "Única"


def test_obtener_nota_inexistente_devuelve_404(cliente: TestClient) -> None:
    respuesta = cliente.get("/notas/999")
    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "Nota no encontrada"


def test_obtener_nota_con_id_no_numerico_devuelve_422(cliente: TestClient) -> None:
    assert cliente.get("/notas/abc").status_code == 422


# ------------------------------------------------------------ actualización


def test_actualizar_nota(cliente: TestClient, crear_nota: CrearNota) -> None:
    crear_nota()
    respuesta = cliente.put("/notas/1", json={"titulo": "Editada", "contenido": "Nuevo contenido"})
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["titulo"] == "Editada"
    assert datos["contenido"] == "Nuevo contenido"


def test_actualizar_conserva_fecha_de_creacion(cliente: TestClient, crear_nota: CrearNota) -> None:
    original = crear_nota().json()
    datos = cliente.put("/notas/1", json={"titulo": "Otra", "contenido": "Texto"}).json()
    assert datos["creada"] == original["creada"]
    actualizada = datetime.fromisoformat(datos["actualizada"])
    creada = datetime.fromisoformat(datos["creada"])
    assert actualizada >= creada


def test_actualizar_nota_inexistente_devuelve_404(cliente: TestClient) -> None:
    respuesta = cliente.put("/notas/999", json={"titulo": "X", "contenido": "Y"})
    assert respuesta.status_code == 404


# -------------------------------------------------------------- eliminación


def test_eliminar_nota(cliente: TestClient, crear_nota: CrearNota) -> None:
    crear_nota()
    assert cliente.delete("/notas/1").status_code == 204
    assert cliente.get("/notas/1").status_code == 404


def test_eliminar_nota_inexistente_devuelve_404(cliente: TestClient) -> None:
    assert cliente.delete("/notas/999").status_code == 404


# ----------------------------------------------------------------- búsqueda


def test_buscar_por_titulo(cliente: TestClient, crear_nota: CrearNota) -> None:
    crear_nota("Lista de compras", "pan y leche")
    crear_nota("Ideas", "proyecto nuevo")
    resultados = cliente.get("/notas", params={"buscar": "compras"}).json()
    assert len(resultados) == 1
    assert resultados[0]["titulo"] == "Lista de compras"


def test_buscar_por_contenido(cliente: TestClient, crear_nota: CrearNota) -> None:
    crear_nota("Lista de compras", "pan y leche")
    crear_nota("Ideas", "proyecto nuevo")
    resultados = cliente.get("/notas", params={"buscar": "proyecto"}).json()
    assert len(resultados) == 1
    assert resultados[0]["titulo"] == "Ideas"


def test_buscar_sin_resultados(cliente: TestClient, crear_nota: CrearNota) -> None:
    crear_nota("Lista de compras", "pan y leche")
    assert cliente.get("/notas", params={"buscar": "inexistente"}).json() == []


# --------------------------------------------------------------- paginación


def test_paginacion_limite(cliente: TestClient, crear_nota: CrearNota) -> None:
    for numero in range(5):
        crear_nota(f"Nota {numero}")
    resultados = cliente.get("/notas", params={"limite": 2}).json()
    assert [nota["titulo"] for nota in resultados] == ["Nota 0", "Nota 1"]


def test_paginacion_desplazamiento(cliente: TestClient, crear_nota: CrearNota) -> None:
    for numero in range(5):
        crear_nota(f"Nota {numero}")
    resultados = cliente.get("/notas", params={"desplazamiento": 3}).json()
    assert [nota["titulo"] for nota in resultados] == ["Nota 3", "Nota 4"]


def test_paginacion_combinada(cliente: TestClient, crear_nota: CrearNota) -> None:
    for numero in range(5):
        crear_nota(f"Nota {numero}")
    parametros = {"limite": 2, "desplazamiento": 2}
    resultados = cliente.get("/notas", params=parametros).json()
    assert [nota["titulo"] for nota in resultados] == ["Nota 2", "Nota 3"]


def test_paginacion_con_busqueda(cliente: TestClient, crear_nota: CrearNota) -> None:
    for numero in range(4):
        crear_nota(f"Tarea {numero}")
    crear_nota("Otra cosa")
    parametros = {"buscar": "Tarea", "limite": 2, "desplazamiento": 2}
    resultados = cliente.get("/notas", params=parametros).json()
    assert [nota["titulo"] for nota in resultados] == ["Tarea 2", "Tarea 3"]


@pytest.mark.parametrize("limite", [0, -1, 101])
def test_limite_fuera_de_rango_devuelve_422(cliente: TestClient, limite: int) -> None:
    assert cliente.get("/notas", params={"limite": limite}).status_code == 422


def test_desplazamiento_negativo_devuelve_422(cliente: TestClient) -> None:
    assert cliente.get("/notas", params={"desplazamiento": -1}).status_code == 422


# --------------------------------------------------------------- validación


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"titulo": "", "contenido": "algo"},
        {"titulo": "algo", "contenido": ""},
        {"titulo": "x" * 101, "contenido": "algo"},
        {"titulo": "algo", "contenido": "x" * 5001},
        {"titulo": "sin contenido"},
        {"contenido": "sin título"},
        {},
    ],
)
def test_crear_nota_invalida_devuelve_422(cliente: TestClient, cuerpo: dict) -> None:
    assert cliente.post("/notas", json=cuerpo).status_code == 422


def test_actualizar_nota_invalida_devuelve_422(cliente: TestClient, crear_nota: CrearNota) -> None:
    crear_nota()
    respuesta = cliente.put("/notas/1", json={"titulo": "", "contenido": "algo"})
    assert respuesta.status_code == 422


def test_crear_nota_en_limites_de_longitud(crear_nota: CrearNota) -> None:
    respuesta = crear_nota("t" * 100, "c" * 5000)
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert len(datos["titulo"]) == 100
    assert len(datos["contenido"]) == 5000
