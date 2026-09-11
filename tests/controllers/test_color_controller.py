"""
Pruebas unitarias para ColorController (Controlador de Colores).

Verifica la consulta del catálogo cromático en base de datos,
la referencia estática de rangos decimales (LISTA_COLORES) y
la obtención de colores individuales por ID.
"""

import pytest
from controllers.color_controller import ColorController
from models.color import Color
from models.num_historia_utils import LISTA_COLORES


def test_listar_colores(patch_conexion):
    """Verifica que listar_colores devuelva los 10 colores registrados en la BD."""
    controller = ColorController()
    colores = controller.listar_colores()

    assert len(colores) == 10
    assert all(isinstance(c, Color) for c in colores)
    nombres = [c.valor for c in colores]
    assert "Marron" in nombres
    assert "Naranja" in nombres
    assert "Azul Celeste" in nombres


def test_obtener_referencia_colores():
    """Verifica que obtener_referencia_colores devuelva la tabla completa sin consultar la BD."""
    controller = ColorController()
    referencia = controller.obtener_referencia_colores()

    assert referencia == LISTA_COLORES
    assert len(referencia) == 10
    assert referencia[0]["rango"] == "00-09"
    assert referencia[0]["nombre"] == "Marron"
    assert referencia[3]["rango"] == "30-39"
    assert referencia[3]["nombre"] == "Naranja"
    assert referencia[9]["rango"] == "90-99"
    assert referencia[9]["nombre"] == "Azul Celeste"


def test_obtener_color_existente(patch_conexion):
    """Verifica la obtención de un color por ID válido."""
    controller = ColorController()
    colores = controller.listar_colores()
    primer_color = colores[0]

    color = controller.obtener_color(primer_color.id)
    assert color is not None
    assert isinstance(color, Color)
    assert color.id == primer_color.id
    assert color.valor == primer_color.valor


def test_obtener_color_inexistente(patch_conexion):
    """Verifica que retorne None si el color consultado no existe."""
    controller = ColorController()
    color = controller.obtener_color(99999)
    assert color is None
