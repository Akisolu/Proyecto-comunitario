"""
Pruebas unitarias para el módulo de utilidades de fechas.

Módulo bajo prueba: utils.date_utils
Valida:
    - Parseo de fechas en formatos DD/MM/YYYY, DD-MM-YYYY y YYYY-MM-DD
    - Normalización a formato ISO (YYYY-MM-DD) y rango válido de años (1900-2100)
    - Formateo para visualización en interfaz y campos de entrada
    - Normalización y generación de patrones para búsquedas flexibles
"""

from datetime import date
import pytest

from utils.date_utils import (
    ACCEPTED_DATE_FORMATS,
    parse_date,
    normalizar_fecha_a_iso,
    formatear_fecha_para_mostrar,
    formatear_fecha_para_entrada,
    normalizar_fecha_para_busqueda,
    generar_patrones_busqueda_fecha,
)


def test_parse_date_formato_barra():
    """Verifica el parseo correcto de fechas con formato DD/MM/YYYY."""
    resultado = parse_date("15/05/2000")
    assert resultado == date(2000, 5, 15)


def test_parse_date_formato_guion():
    """Verifica el parseo correcto de fechas con formato DD-MM-YYYY."""
    resultado = parse_date("15-05-2000")
    assert resultado == date(2000, 5, 15)


def test_parse_date_formato_iso():
    """Verifica el parseo correcto de fechas con formato ISO YYYY-MM-DD."""
    resultado = parse_date("2000-05-15")
    assert resultado == date(2000, 5, 15)


def test_parse_date_none():
    """Verifica que parse_date lance ValueError cuando el argumento es None."""
    with pytest.raises(ValueError, match="Fecha no puede ser None"):
        parse_date(None)


def test_parse_date_vacio():
    """Verifica que parse_date lance ValueError cuando la cadena está vacía o contiene solo espacios."""
    with pytest.raises(ValueError, match="Fecha no puede estar vacia"):
        parse_date("")

    with pytest.raises(ValueError, match="Fecha no puede estar vacia"):
        parse_date("   ")


def test_parse_date_invalido():
    """Verifica que parse_date lance ValueError ante valores que no son fechas válidas."""
    with pytest.raises(ValueError, match="Formato de fecha invalido"):
        parse_date("fecha_invalida")

    with pytest.raises(ValueError, match="Formato de fecha invalido"):
        parse_date("32/01/2020")

    with pytest.raises(ValueError, match="Formato de fecha invalido"):
        parse_date("2020-02-30")


def test_normalizar_iso_desde_barra():
    """Verifica la normalización a ISO YYYY-MM-DD a partir de DD/MM/YYYY."""
    assert normalizar_fecha_a_iso("15/05/2000") == "2000-05-15"


def test_normalizar_iso_desde_guion():
    """Verifica la normalización a ISO YYYY-MM-DD a partir de DD-MM-YYYY."""
    assert normalizar_fecha_a_iso("15-05-2000") == "2000-05-15"


def test_normalizar_iso_passthrough():
    """Verifica que una fecha ya en formato ISO se conserve sin cambios."""
    assert normalizar_fecha_a_iso("2000-05-15") == "2000-05-15"


def test_normalizar_iso_anio_invalido():
    """Verifica que años fuera del rango 1900-2100 generen ValueError."""
    with pytest.raises(ValueError, match="Anio invalido"):
        normalizar_fecha_a_iso("15-05-1899")

    with pytest.raises(ValueError, match="Anio invalido"):
        normalizar_fecha_a_iso("15-05-2101")

    with pytest.raises(ValueError, match="Anio invalido"):
        normalizar_fecha_a_iso("1800-01-01")


def test_formatear_mostrar_desde_iso():
    """Verifica la conversión de fecha ISO a formato visual DD-MM-YYYY."""
    assert formatear_fecha_para_mostrar("2000-05-15") == "15-05-2000"


def test_formatear_mostrar_desde_date():
    """Verifica la conversión de un objeto date a formato visual DD-MM-YYYY."""
    assert formatear_fecha_para_mostrar(date(2000, 5, 15)) == "15-05-2000"


def test_formatear_entrada_guion():
    """Verifica formatear_fecha_para_entrada con separador '-' para str y date."""
    assert formatear_fecha_para_entrada("2000-05-15", separador="-") == "15-05-2000"
    assert formatear_fecha_para_entrada(date(2000, 5, 15), separador="-") == "15-05-2000"


def test_formatear_entrada_barra():
    """Verifica formatear_fecha_para_entrada con separador '/' para str y date."""
    assert formatear_fecha_para_entrada("2000-05-15", separador="/") == "15/05/2000"
    assert formatear_fecha_para_entrada(date(2000, 5, 15), separador="/") == "15/05/2000"


def test_normalizar_busqueda_valido():
    """Verifica que normalizar_fecha_para_busqueda convierta fechas completas a formato ISO."""
    assert normalizar_fecha_para_busqueda("15/05/2000") == "2000-05-15"
    assert normalizar_fecha_para_busqueda("15-05-2000") == "2000-05-15"
    assert normalizar_fecha_para_busqueda("2000-05-15") == "2000-05-15"


def test_normalizar_busqueda_parcial():
    """Verifica que normalizar_fecha_para_busqueda devuelva el texto intacto ante búsquedas parciales."""
    assert normalizar_fecha_para_busqueda("mayo") == "mayo"
    assert normalizar_fecha_para_busqueda("2000") == "2000"
    assert normalizar_fecha_para_busqueda("15/05") == "15/05"


def test_generar_patrones_fecha_completa():
    """Verifica que generar_patrones_busqueda_fecha retorne [iso, dash, slash] para fechas completas."""
    esperado = ["2000-05-15", "15-05-2000", "15/05/2000"]
    assert generar_patrones_busqueda_fecha("15/05/2000") == esperado
    assert generar_patrones_busqueda_fecha("15-05-2000") == esperado
    assert generar_patrones_busqueda_fecha("2000-05-15") == esperado


def test_generar_patrones_fecha_parcial():
    """Verifica que generar_patrones_busqueda_fecha retorne una lista con el valor original si es parcial."""
    assert generar_patrones_busqueda_fecha("2000") == ["2000"]
    assert generar_patrones_busqueda_fecha("mayo") == ["mayo"]


def test_generar_patrones_fecha_vacia():
    """Verifica que generar_patrones_busqueda_fecha retorne lista vacía para cadenas vacías o espacios."""
    assert generar_patrones_busqueda_fecha("") == []
    assert generar_patrones_busqueda_fecha("   ") == []
