"""
Pruebas unitarias para el módulo de utilidades de número de historia clínica.

Módulo bajo prueba: models.num_historia_utils
Valida:
    - Validación del formato XX-XX-XX
    - Mapeo cromático según la decena del último par
    - Funciones auxiliares de obtención de color y nombre
"""

import pytest

from models.num_historia_utils import (
    PATRON_NUM_HISTORIA,
    MAPA_COLORES,
    LISTA_COLORES,
    validar_formato_num_historia,
    obtener_color_por_num_historia,
    obtener_nombre_color,
)


def test_formato_valido():
    """Verifica que números de historia con formato correcto XX-XX-XX sean aceptados."""
    assert validar_formato_num_historia("03-77-34") is True
    assert validar_formato_num_historia("00-00-00") is True
    assert validar_formato_num_historia("99-99-99") is True
    assert validar_formato_num_historia("12-34-56") is True


def test_formato_invalido_letras():
    """Verifica que se rechacen números de historia que contengan caracteres alfabéticos."""
    assert validar_formato_num_historia("03-77-3A") is False
    assert validar_formato_num_historia("AB-CD-EF") is False
    assert validar_formato_num_historia("1A-2B-3C") is False
    assert validar_formato_num_historia("00-00-0X") is False


def test_formato_invalido_longitud():
    """Verifica que se rechacen cadenas con cantidad de dígitos o estructura incorrecta."""
    assert validar_formato_num_historia("1-2-3") is False
    assert validar_formato_num_historia("037734") is False
    assert validar_formato_num_historia("003-77-34") is False
    assert validar_formato_num_historia("03-7-34") is False
    assert validar_formato_num_historia("03-77-345") is False
    assert validar_formato_num_historia("03-77-3") is False


def test_formato_invalido_vacio():
    """Verifica que cadenas vacías o valores nulos sean rechazados apropiadamente."""
    assert validar_formato_num_historia("") is False
    try:
        resultado = validar_formato_num_historia(None)
        assert resultado is False
    except (TypeError, AttributeError):
        # re.match requiere str o bytes-like; lanzar TypeError también es un rechazo válido
        pass


def test_mapeo_cromatico_todas_decenas():
    """Verifica que cada decena (0 a 9) mapee al nombre de color y código hexadecimal correctos."""
    for d in range(10):
        num_historia = f"00-00-{d}0"
        color_info = obtener_color_por_num_historia(num_historia)
        nombre_esperado, hex_esperado = MAPA_COLORES[d]
        assert color_info["nombre"] == nombre_esperado
        assert color_info["hex"] == hex_esperado

        # Verifica también con la unidad más alta de la decena (ej: 09, 19, ..., 99)
        num_historia_unidad = f"12-34-{d}9"
        color_info_unidad = obtener_color_por_num_historia(num_historia_unidad)
        assert color_info_unidad["nombre"] == nombre_esperado
        assert color_info_unidad["hex"] == hex_esperado


def test_color_num_historia_frontera_inferior():
    """Verifica el caso frontera inferior: '00-00-00' corresponde a Marrón."""
    color_info = obtener_color_por_num_historia("00-00-00")
    assert color_info["nombre"] == "Marron"
    assert color_info["hex"] == "#8B4513"


def test_color_num_historia_frontera_superior():
    """Verifica el caso frontera superior: '00-00-99' corresponde a Azul Celeste."""
    color_info = obtener_color_por_num_historia("00-00-99")
    assert color_info["nombre"] == "Azul Celeste"
    assert color_info["hex"] == "#87CEEB"


def test_error_color_formato_invalido():
    """Verifica que se lance ValueError al intentar obtener el color de un formato inválido."""
    with pytest.raises(ValueError, match="Formato de numero de historia invalido"):
        obtener_color_por_num_historia("invalid")

    with pytest.raises(ValueError):
        obtener_color_por_num_historia("03-77-3A")

    with pytest.raises(ValueError):
        obtener_color_por_num_historia("")

    with pytest.raises(ValueError):
        obtener_color_por_num_historia("037734")


def test_obtener_nombre_color():
    """Verifica la función atajo obtener_nombre_color con distintos números de historia."""
    assert obtener_nombre_color("03-77-34") == "Naranja"
    assert obtener_nombre_color("00-00-05") == "Marron"
    assert obtener_nombre_color("11-22-15") == "Azul Marino"
    assert obtener_nombre_color("99-88-29") == "Verde"
    assert obtener_nombre_color("01-02-40") == "Morado"
    assert obtener_nombre_color("05-05-55") == "Rosa"
    assert obtener_nombre_color("06-06-61") == "Turquesa"
    assert obtener_nombre_color("07-07-77") == "Amarillo"
    assert obtener_nombre_color("08-08-83") == "Rojo"
    assert obtener_nombre_color("09-09-92") == "Azul Celeste"
