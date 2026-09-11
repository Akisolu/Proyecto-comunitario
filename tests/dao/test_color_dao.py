"""
Pruebas unitarias para ColorDAO (Acceso a Datos de Colores).

Verifica el ciclo de vida CRUD de los colores en la base de datos:
creación, consulta por ID, consulta por nombre, actualización de valores
y desactivación lógica (soft delete).
"""

import pytest
from dao.color import ColorDAO
from models.color import ColorBase, Color


def test_obtener_todos_colores(patch_conexion):
    """Verifica que obtener_todos retorne los 10 colores base sembrados en conftest."""
    dao = ColorDAO()
    colores = dao.obtener_todos()

    assert len(colores) == 10
    assert all(isinstance(c, Color) for c in colores)


def test_crear_color_exitoso(patch_conexion):
    """Verifica la inserción de un nuevo color en la base de datos."""
    dao = ColorDAO()
    nuevo = ColorBase(valor="Dorado")
    id_color = dao.crear(nuevo)

    assert id_color > 0

    color_creado = dao.obtener_por_id(id_color)
    assert color_creado is not None
    assert color_creado.valor == "Dorado"
    assert color_creado.estado == 1


def test_obtener_por_id_existente_e_inexistente(patch_conexion):
    """Verifica la recuperación por ID tanto para registros existentes como inexistentes."""
    dao = ColorDAO()
    todos = dao.obtener_todos()
    primer_id = todos[0].id

    color = dao.obtener_por_id(primer_id)
    assert color is not None
    assert color.id == primer_id

    inexistente = dao.obtener_por_id(99999)
    assert inexistente is None


def test_obtener_por_valor(patch_conexion):
    """Verifica la búsqueda de color por su nombre textual exacto."""
    dao = ColorDAO()
    color = dao.obtener_por_valor("Verde")

    assert color is not None
    assert color.valor == "Verde"

    inexistente = dao.obtener_por_valor("ColorInexistenteXYZ")
    assert inexistente is None


def test_actualizar_color(patch_conexion):
    """Verifica la actualización del nombre de un color activo."""
    dao = ColorDAO()
    # Crear un color temporal para actualizar
    id_temp = dao.crear(ColorBase(valor="Gris Claro"))

    color_mod = ColorBase(valor="Gris Plata")
    exito = dao.actualizar(id_temp, color_mod)
    assert exito is True

    actualizado = dao.obtener_por_id(id_temp)
    assert actualizado.valor == "Gris Plata"


def test_soft_delete_color(patch_conexion):
    """Verifica que soft_delete desactive el color (estado = 0) y lo excluya de consultas activas."""
    dao = ColorDAO()
    id_temp = dao.crear(ColorBase(valor="Violeta"))

    exito = dao.soft_delete(id_temp)
    assert exito is True

    # Comprobar que ya no aparece en consultas activas
    assert dao.obtener_por_id(id_temp) is None
    assert dao.obtener_por_valor("Violeta") is None

    todos = dao.obtener_todos()
    assert not any(c.id == id_temp for c in todos)
