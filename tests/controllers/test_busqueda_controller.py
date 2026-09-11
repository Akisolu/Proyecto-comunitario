"""
Pruebas unitarias para BusquedaController (Controlador de Búsquedas).

Verifica el manejo de los criterios de búsqueda (todos, cédula, nombres,
apellidos, fecha de nacimiento, lugar de nacimiento, número de historia),
búsqueda multi-criterio, paginación y captura controlada de excepciones.
"""

import pytest
from controllers.busqueda_controller import BusquedaController
from models.busqueda import TarjetaSalida


def test_buscar_campo_vacio(patch_conexion):
    """Verifica que se exija un valor de búsqueda para criterios distintos a 'todos'."""
    controller = BusquedaController()

    exito, msg = controller.buscar("cedula", "")
    assert exito is False
    assert "Debe ingresar un valor de búsqueda" in msg

    exito, msg = controller.buscar("apellido", "   ")
    assert exito is False
    assert "Debe ingresar un valor de búsqueda" in msg


def test_buscar_criterio_invalido(patch_conexion):
    """Verifica que se rechacen criterios no soportados."""
    controller = BusquedaController()

    exito, msg = controller.buscar("criterio_desconocido", "prueba")
    assert exito is False
    assert "Criterio de búsqueda no válido" in msg


def test_buscar_criterio_todos(paciente_con_tarjeta):
    """Verifica la búsqueda bajo el criterio 'todos'."""
    controller = BusquedaController()

    exito, (resultados, total) = controller.buscar("todos", "")
    assert exito is True
    assert total >= 1
    assert len(resultados) >= 1
    assert isinstance(resultados[0], TarjetaSalida)


def test_buscar_por_cedula(paciente_con_tarjeta):
    """Verifica la búsqueda por cédula a través del controlador."""
    controller = BusquedaController()

    exito, (resultados, total) = controller.buscar("cedula", "12345")
    assert exito is True
    assert total == 1
    assert resultados[0].cedula == "V-12345678"


def test_buscar_por_nombre_completo(paciente_con_tarjeta):
    """Verifica la búsqueda por nombre completo a través del controlador."""
    controller = BusquedaController()

    exito, (resultados, total) = controller.buscar("nombre_completo", "María González")
    assert exito is True
    assert total == 1
    assert resultados[0].nombre1 == "María"


def test_buscar_por_apellido(paciente_con_tarjeta):
    """Verifica la búsqueda por apellido a través del controlador."""
    controller = BusquedaController()

    exito, (resultados, total) = controller.buscar("apellido", "González")
    assert exito is True
    assert total == 1
    assert resultados[0].apellido1 == "González"


def test_buscar_por_fecha_nacimiento(paciente_con_tarjeta):
    """Verifica la búsqueda por fecha de nacimiento a través del controlador."""
    controller = BusquedaController()

    exito, (resultados, total) = controller.buscar("fecha_nacimiento", "15/05/1990")
    assert exito is True
    assert total == 1


def test_buscar_por_lugar_nacimiento(paciente_con_tarjeta):
    """Verifica la búsqueda por lugar de nacimiento a través del controlador."""
    controller = BusquedaController()

    exito, (resultados, total) = controller.buscar("lugar_nacimiento", "Turén")
    assert exito is True
    assert total == 1
    assert resultados[0].lugar_nacimiento == "Turén"


def test_buscar_por_num_historia(paciente_con_tarjeta):
    """Verifica la búsqueda por número de historia a través del controlador."""
    controller = BusquedaController()

    exito, (resultados, total) = controller.buscar("num_historia", "03-77-34")
    assert exito is True
    assert total == 1
    assert resultados[0].num_historia == "03-77-34"


def test_obtener_todos_directo(paciente_con_tarjeta):
    """Verifica el método obtener_todos del controlador con paginación."""
    controller = BusquedaController()

    resultados, total = controller.obtener_todos(limit=10, offset=0)
    assert total >= 1
    assert len(resultados) >= 1
    assert isinstance(resultados[0], TarjetaSalida)


def test_buscar_multicriterio_exitoso(paciente_con_tarjeta):
    """Verifica la búsqueda multi-criterio combinando filtros."""
    controller = BusquedaController()

    filtros = {
        "nombre": "María",
        "apellido": "González",
        "lugar_nacimiento": "Turén",
    }
    exito, (resultados, total) = controller.buscar_multicriterio(filtros)
    assert exito is True
    assert total == 1
    assert resultados[0].cedula == "V-12345678"


def test_buscar_manejo_excepcion(patch_conexion, monkeypatch):
    """Verifica que las excepciones internas del DAO se capturen de forma segura."""
    controller = BusquedaController()

    def _fake_buscar_cedula(*args, **kwargs):
        raise RuntimeError("Fallo simulado en motor FTS5")

    monkeypatch.setattr(controller.busqueda_dao, "buscar_por_cedula", _fake_buscar_cedula)

    exito, msg = controller.buscar("cedula", "12345")
    assert exito is False
    assert "Error al realizar la búsqueda: Fallo simulado en motor FTS5" in msg


def test_buscar_multicriterio_manejo_excepcion(patch_conexion, monkeypatch):
    """Verifica que las excepciones en búsqueda multi-criterio se capturen ordenadamente."""
    controller = BusquedaController()

    def _fake_multi(*args, **kwargs):
        raise ValueError("Error de sintaxis SQL en multicriterio")

    monkeypatch.setattr(controller.busqueda_dao, "buscar_multicriterio", _fake_multi)

    exito, msg = controller.buscar_multicriterio({"cedula": "1234"})
    assert exito is False
    assert "Error al realizar la búsqueda multi-criterio" in msg
