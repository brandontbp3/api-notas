"""Tests de la API de notas: CRUD, etiquetas, búsqueda, ordenamiento y paginación."""

from collections.abc import Callable
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from api_notas.modelos import Etiqueta

CrearNota = Callable[..., Response]


def _etiquetas_en_bd(fabrica_sesiones: sessionmaker[Session]) -> list[str]:
    """Devuelve los nombres de todas las etiquetas guardadas en la base."""
    with fabrica_sesiones() as sesion:
        return sorted(sesion.scalars(select(Etiqueta.nombre)).all())


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


# ---------------------------------------------------------------- etiquetas


def test_crear_nota_con_etiquetas(crear_nota: CrearNota) -> None:
    respuesta = crear_nota("Con etiquetas", etiquetas=["trabajo", "ideas"])
    assert respuesta.status_code == 201
    assert respuesta.json()["etiquetas"] == ["trabajo", "ideas"]


def test_crear_nota_sin_etiquetas_devuelve_lista_vacia(crear_nota: CrearNota) -> None:
    assert crear_nota().json()["etiquetas"] == []


def test_etiquetas_se_normalizan_a_minusculas(crear_nota: CrearNota) -> None:
    datos = crear_nota(etiquetas=["Trabajo", "IDEAS"]).json()
    assert datos["etiquetas"] == ["trabajo", "ideas"]


def test_etiquetas_duplicadas_se_descartan(crear_nota: CrearNota) -> None:
    datos = crear_nota(etiquetas=["trabajo", "Trabajo", "ideas", "ideas"]).json()
    assert datos["etiquetas"] == ["trabajo", "ideas"]


def test_etiquetas_compartidas_se_guardan_una_sola_vez(
    crear_nota: CrearNota, fabrica_sesiones: sessionmaker[Session]
) -> None:
    crear_nota("Primera", etiquetas=["trabajo"])
    crear_nota("Segunda", etiquetas=["trabajo"])
    assert _etiquetas_en_bd(fabrica_sesiones) == ["trabajo"]


def test_crear_nota_en_limites_de_etiquetas(crear_nota: CrearNota) -> None:
    etiquetas = [f"{'e' * 29}{numero}" for numero in range(10)]
    respuesta = crear_nota(etiquetas=etiquetas)
    assert respuesta.status_code == 201
    assert respuesta.json()["etiquetas"] == etiquetas


@pytest.mark.parametrize(
    "etiquetas",
    [
        [""],
        ["x" * 31],
        [f"etiqueta{numero}" for numero in range(11)],
        ["válida", ""],
        "no es una lista",
    ],
)
def test_crear_nota_con_etiquetas_invalidas_devuelve_422(
    cliente: TestClient, etiquetas: object
) -> None:
    cuerpo = {"titulo": "Nota", "contenido": "Texto", "etiquetas": etiquetas}
    assert cliente.post("/notas", json=cuerpo).status_code == 422


def test_filtrar_por_etiqueta(cliente: TestClient, crear_nota: CrearNota) -> None:
    crear_nota("Del trabajo", etiquetas=["trabajo"])
    crear_nota("Personal", etiquetas=["personal"])
    crear_nota("Sin etiquetas")
    resultados = cliente.get("/notas", params={"etiqueta": "trabajo"}).json()
    assert [nota["titulo"] for nota in resultados] == ["Del trabajo"]


def test_filtrar_por_etiqueta_no_distingue_mayusculas(
    cliente: TestClient, crear_nota: CrearNota
) -> None:
    crear_nota("Del trabajo", etiquetas=["trabajo"])
    resultados = cliente.get("/notas", params={"etiqueta": "TRABAJO"}).json()
    assert [nota["titulo"] for nota in resultados] == ["Del trabajo"]


def test_filtrar_por_etiqueta_sin_resultados(cliente: TestClient, crear_nota: CrearNota) -> None:
    crear_nota("Del trabajo", etiquetas=["trabajo"])
    assert cliente.get("/notas", params={"etiqueta": "inexistente"}).json() == []


def test_filtrar_por_etiqueta_combinado_con_busqueda(
    cliente: TestClient, crear_nota: CrearNota
) -> None:
    crear_nota("Informe mensual", etiquetas=["trabajo"])
    crear_nota("Informe anual", etiquetas=["personal"])
    crear_nota("Recordatorio", etiquetas=["trabajo"])
    parametros = {"buscar": "Informe", "etiqueta": "trabajo"}
    resultados = cliente.get("/notas", params=parametros).json()
    assert [nota["titulo"] for nota in resultados] == ["Informe mensual"]


def test_eliminar_nota_borra_etiquetas_huerfanas(
    cliente: TestClient, crear_nota: CrearNota, fabrica_sesiones: sessionmaker[Session]
) -> None:
    crear_nota("Única", etiquetas=["solitaria"])
    assert cliente.delete("/notas/1").status_code == 204
    assert _etiquetas_en_bd(fabrica_sesiones) == []


def test_etiqueta_compartida_no_se_borra_si_sigue_en_uso(
    cliente: TestClient, crear_nota: CrearNota, fabrica_sesiones: sessionmaker[Session]
) -> None:
    crear_nota("Primera", etiquetas=["compartida", "propia"])
    crear_nota("Segunda", etiquetas=["compartida"])
    cliente.delete("/notas/1")
    assert _etiquetas_en_bd(fabrica_sesiones) == ["compartida"]


def test_put_borra_etiquetas_que_quedan_huerfanas(
    cliente: TestClient, crear_nota: CrearNota, fabrica_sesiones: sessionmaker[Session]
) -> None:
    crear_nota("Nota", etiquetas=["vieja"])
    cuerpo = {"titulo": "Nota", "contenido": "Texto", "etiquetas": ["nueva"]}
    cliente.put("/notas/1", json=cuerpo)
    assert _etiquetas_en_bd(fabrica_sesiones) == ["nueva"]


def test_put_reemplaza_etiquetas(cliente: TestClient, crear_nota: CrearNota) -> None:
    crear_nota(etiquetas=["trabajo", "ideas"])
    cuerpo = {"titulo": "Editada", "contenido": "Texto", "etiquetas": ["personal"]}
    assert cliente.put("/notas/1", json=cuerpo).json()["etiquetas"] == ["personal"]


def test_put_sin_etiquetas_las_elimina(cliente: TestClient, crear_nota: CrearNota) -> None:
    crear_nota(etiquetas=["trabajo"])
    datos = cliente.put("/notas/1", json={"titulo": "Editada", "contenido": "Texto"}).json()
    assert datos["etiquetas"] == []


# ------------------------------------------------------ actualización parcial


def test_patch_solo_titulo(cliente: TestClient, crear_nota: CrearNota) -> None:
    crear_nota("Original", "Contenido original", etiquetas=["trabajo"])
    respuesta = cliente.patch("/notas/1", json={"titulo": "Nuevo título"})
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["titulo"] == "Nuevo título"
    assert datos["contenido"] == "Contenido original"
    assert datos["etiquetas"] == ["trabajo"]


def test_patch_solo_contenido(cliente: TestClient, crear_nota: CrearNota) -> None:
    crear_nota("Original", "Contenido original")
    datos = cliente.patch("/notas/1", json={"contenido": "Contenido nuevo"}).json()
    assert datos["titulo"] == "Original"
    assert datos["contenido"] == "Contenido nuevo"


def test_patch_solo_etiquetas(cliente: TestClient, crear_nota: CrearNota) -> None:
    crear_nota("Original", "Contenido original", etiquetas=["vieja"])
    datos = cliente.patch("/notas/1", json={"etiquetas": ["Nueva"]}).json()
    assert datos["titulo"] == "Original"
    assert datos["contenido"] == "Contenido original"
    assert datos["etiquetas"] == ["nueva"]


def test_patch_varios_campos(cliente: TestClient, crear_nota: CrearNota) -> None:
    crear_nota()
    cuerpo = {"titulo": "Nuevo", "contenido": "Texto nuevo", "etiquetas": ["ideas"]}
    datos = cliente.patch("/notas/1", json=cuerpo).json()
    assert datos["titulo"] == "Nuevo"
    assert datos["contenido"] == "Texto nuevo"
    assert datos["etiquetas"] == ["ideas"]


def test_patch_lista_vacia_quita_las_etiquetas(cliente: TestClient, crear_nota: CrearNota) -> None:
    crear_nota(etiquetas=["trabajo"])
    assert cliente.patch("/notas/1", json={"etiquetas": []}).json()["etiquetas"] == []


def test_patch_actualiza_fecha_y_conserva_creada(
    cliente: TestClient, crear_nota: CrearNota
) -> None:
    original = crear_nota().json()
    datos = cliente.patch("/notas/1", json={"titulo": "Otra"}).json()
    assert datos["creada"] == original["creada"]
    actualizada = datetime.fromisoformat(datos["actualizada"])
    original_actualizada = datetime.fromisoformat(original["actualizada"])
    assert actualizada >= original_actualizada


def test_patch_sin_campos_devuelve_422(cliente: TestClient, crear_nota: CrearNota) -> None:
    crear_nota()
    assert cliente.patch("/notas/1", json={}).status_code == 422


def test_patch_nota_inexistente_devuelve_404(cliente: TestClient) -> None:
    respuesta = cliente.patch("/notas/999", json={"titulo": "X"})
    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "Nota no encontrada"


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"titulo": ""},
        {"titulo": "x" * 101},
        {"contenido": ""},
        {"contenido": "x" * 5001},
        {"etiquetas": [""]},
        {"etiquetas": ["x" * 31]},
        {"etiquetas": [f"etiqueta{numero}" for numero in range(11)]},
    ],
)
def test_patch_invalido_devuelve_422(
    cliente: TestClient, crear_nota: CrearNota, cuerpo: dict
) -> None:
    crear_nota()
    assert cliente.patch("/notas/1", json=cuerpo).status_code == 422


def test_patch_no_borra_etiquetas_si_no_se_envian(
    cliente: TestClient, crear_nota: CrearNota, fabrica_sesiones: sessionmaker[Session]
) -> None:
    crear_nota(etiquetas=["trabajo"])
    cliente.patch("/notas/1", json={"titulo": "Otra"})
    assert _etiquetas_en_bd(fabrica_sesiones) == ["trabajo"]


# ------------------------------------------------------------- ordenamiento


def test_ordenar_por_titulo_ascendente(cliente: TestClient, crear_nota: CrearNota) -> None:
    crear_nota("Zanahoria")
    crear_nota("Ajo")
    crear_nota("Melón")
    resultados = cliente.get("/notas", params={"ordenar": "titulo"}).json()
    assert [nota["titulo"] for nota in resultados] == ["Ajo", "Melón", "Zanahoria"]


def test_ordenar_por_titulo_descendente(cliente: TestClient, crear_nota: CrearNota) -> None:
    crear_nota("Ajo")
    crear_nota("Zanahoria")
    crear_nota("Melón")
    parametros = {"ordenar": "titulo", "direccion": "desc"}
    resultados = cliente.get("/notas", params=parametros).json()
    assert [nota["titulo"] for nota in resultados] == ["Zanahoria", "Melón", "Ajo"]


def test_ordenar_por_defecto_por_id(cliente: TestClient, crear_nota: CrearNota) -> None:
    crear_nota("Primera")
    crear_nota("Segunda")
    resultados = cliente.get("/notas", params={"direccion": "desc"}).json()
    assert [nota["id"] for nota in resultados] == [2, 1]


def test_ordenar_por_creada_descendente(cliente: TestClient, crear_nota: CrearNota) -> None:
    for numero in range(3):
        crear_nota(f"Nota {numero}")
    parametros = {"ordenar": "creada", "direccion": "desc"}
    resultados = cliente.get("/notas", params=parametros).json()
    fechas = [nota["creada"] for nota in resultados]
    assert fechas == sorted(fechas, reverse=True)


def test_ordenar_por_actualizada_descendente(cliente: TestClient, crear_nota: CrearNota) -> None:
    for numero in range(3):
        crear_nota(f"Nota {numero}")
    cliente.patch("/notas/1", json={"titulo": "Recién tocada"})
    parametros = {"ordenar": "actualizada", "direccion": "desc"}
    resultados = cliente.get("/notas", params=parametros).json()
    assert resultados[0]["id"] == 1
    fechas = [nota["actualizada"] for nota in resultados]
    assert fechas == sorted(fechas, reverse=True)


def test_ordenamiento_combinado_con_busqueda_y_paginacion(
    cliente: TestClient, crear_nota: CrearNota
) -> None:
    for titulo in ["Tarea C", "Tarea A", "Otra cosa", "Tarea B"]:
        crear_nota(titulo)
    parametros = {"buscar": "Tarea", "ordenar": "titulo", "limite": 2}
    resultados = cliente.get("/notas", params=parametros).json()
    assert [nota["titulo"] for nota in resultados] == ["Tarea A", "Tarea B"]


def test_ordenar_invalido_devuelve_422(cliente: TestClient) -> None:
    assert cliente.get("/notas", params={"ordenar": "color"}).status_code == 422


def test_direccion_invalida_devuelve_422(cliente: TestClient) -> None:
    assert cliente.get("/notas", params={"direccion": "diagonal"}).status_code == 422


# ------------------------------------------------------------ X-Total-Count


def test_total_count_sin_paginar(cliente: TestClient, crear_nota: CrearNota) -> None:
    for numero in range(5):
        crear_nota(f"Nota {numero}")
    respuesta = cliente.get("/notas", params={"limite": 2})
    assert respuesta.headers["X-Total-Count"] == "5"
    assert len(respuesta.json()) == 2


def test_total_count_respeta_busqueda(cliente: TestClient, crear_nota: CrearNota) -> None:
    for numero in range(3):
        crear_nota(f"Tarea {numero}")
    crear_nota("Otra cosa")
    respuesta = cliente.get("/notas", params={"buscar": "Tarea", "limite": 1})
    assert respuesta.headers["X-Total-Count"] == "3"
    assert len(respuesta.json()) == 1


def test_total_count_respeta_filtro_de_etiqueta(cliente: TestClient, crear_nota: CrearNota) -> None:
    crear_nota("Primera", etiquetas=["trabajo"])
    crear_nota("Segunda", etiquetas=["trabajo"])
    crear_nota("Tercera", etiquetas=["personal"])
    respuesta = cliente.get("/notas", params={"etiqueta": "trabajo", "limite": 1})
    assert respuesta.headers["X-Total-Count"] == "2"
    assert len(respuesta.json()) == 1


def test_total_count_sin_notas_es_cero(cliente: TestClient) -> None:
    assert cliente.get("/notas").headers["X-Total-Count"] == "0"
