"""
Pruebas unitarias para BusquedaDAO (Capa de Búsqueda Optimizada con Late Join).

Verifica la consulta unificada de pacientes con tarjeta y color, búsquedas FTS5
por cédula, nombre, apellido, nombre completo, búsquedas relacionales por lugar de
nacimiento y número de historia clínica, búsqueda multi-criterio compleja,
desglose de fecha de nacimiento en partes, paginación por páginas y ramas de Late Join.
"""

import pytest
from dao.busqueda import BusquedaDAO
from dao.paciente import PacienteDAO
from dao.tarjeta import TarjetaDAO
from dao.color import ColorDAO
from models.busqueda import TarjetaSalida
from models.paciente import PacienteCreate
from models.tarjeta import TarjetaCreate
from models.num_historia_utils import obtener_color_por_num_historia


def _crear_paciente_con_tarjeta(patch_conexion, cedula_num, nombre, apellido, num_historia, fecha_nac="01/01/2000", lugar="Caracas"):
    """Función auxiliar para registrar un paciente con su correspondiente tarjeta y color."""
    p_dao = PacienteDAO()
    t_dao = TarjetaDAO()
    c_dao = ColorDAO()

    paciente = PacienteCreate(
        cedula=f"V-{cedula_num}" if cedula_num else "S/C",
        nombre1=nombre,
        apellido1=apellido,
        fecha_nacimiento=fecha_nac,
        lugar_nacimiento=lugar,
        estado_vital=1,
    )
    id_p = p_dao.crear(paciente)

    info = obtener_color_por_num_historia(num_historia)
    color = c_dao.obtener_por_valor(info["nombre"])
    assert color is not None

    tarjeta = TarjetaCreate(
        num_historia=num_historia,
        id_paciente=id_p,
        id_color=color.id,
    )
    t_dao.crear(tarjeta)
    return id_p


def test_obtener_todos(paciente_con_tarjeta):
    """Verifica que obtener_todos devuelva la lista de tarjetas activas con total correcto."""
    dao = BusquedaDAO()
    resultados, total = dao.obtener_todos()

    assert total == 1
    assert len(resultados) == 1
    assert isinstance(resultados[0], TarjetaSalida)
    assert resultados[0].id_paciente == paciente_con_tarjeta["id"]
    assert resultados[0].cedula == "V-12345678"
    assert resultados[0].num_historia == "03-77-34"
    assert resultados[0].color == "Naranja"


def test_obtener_todos_sin_datos(patch_conexion):
    """Verifica que obtener_todos retorne lista vacía y total 0 si no hay tarjetas registradas."""
    dao = BusquedaDAO()
    resultados, total = dao.obtener_todos()

    assert total == 0
    assert len(resultados) == 0


def test_buscar_por_cedula(paciente_con_tarjeta):
    """Verifica la búsqueda por fragmento de cédula usando índice FTS5."""
    dao = BusquedaDAO()
    resultados, total = dao.buscar_por_cedula("12345")

    assert total == 1
    assert len(resultados) == 1
    assert resultados[0].id_paciente == paciente_con_tarjeta["id"]
    assert resultados[0].cedula == "V-12345678"


def test_buscar_por_nombre(paciente_con_tarjeta):
    """Verifica la búsqueda por nombre de paciente."""
    dao = BusquedaDAO()
    resultados, total = dao.buscar_por_nombre("María")

    assert total == 1
    assert len(resultados) == 1
    assert resultados[0].nombre1 == "María"


def test_buscar_por_apellido(paciente_con_tarjeta):
    """Verifica la búsqueda por primer apellido de paciente."""
    dao = BusquedaDAO()
    resultados, total = dao.buscar_por_apellido("González")

    assert total == 1
    assert len(resultados) == 1
    assert resultados[0].apellido1 == "González"


def test_buscar_por_nombre_completo(paciente_con_tarjeta):
    """Verifica la búsqueda por coincidencia compuesta de nombre y apellido."""
    dao = BusquedaDAO()
    resultados, total = dao.buscar_por_nombre_completo("María González")

    assert total == 1
    assert len(resultados) == 1
    assert resultados[0].id_paciente == paciente_con_tarjeta["id"]


def test_buscar_por_nombre_completo_vacio(paciente_con_tarjeta):
    """Verifica que buscar_por_nombre_completo con texto en blanco retorne todos los registros."""
    dao = BusquedaDAO()
    resultados, total = dao.buscar_por_nombre_completo("    ")

    assert total == 1
    assert len(resultados) == 1


def test_buscar_por_fecha_nacimiento_valida(paciente_con_tarjeta):
    """Verifica la búsqueda por fecha de nacimiento completa."""
    dao = BusquedaDAO()
    resultados, total = dao.buscar_por_fecha_nacimiento("15/05/1990")

    assert total == 1
    assert len(resultados) == 1
    assert resultados[0].id_paciente == paciente_con_tarjeta["id"]


def test_buscar_por_fecha_nacimiento_vacia():
    """Verifica que buscar_por_fecha_nacimiento con fecha vacía retorne lista vacía."""
    dao = BusquedaDAO()
    resultados, total = dao.buscar_por_fecha_nacimiento("")

    assert total == 0
    assert len(resultados) == 0


def test_buscar_por_lugar(paciente_con_tarjeta):
    """Verifica la búsqueda por lugar de nacimiento."""
    dao = BusquedaDAO()
    resultados, total = dao.buscar_por_lugar_nacimiento("Turén")

    assert total == 1
    assert len(resultados) == 1
    assert resultados[0].lugar_nacimiento == "Turén"


def test_buscar_por_num_historia(paciente_con_tarjeta):
    """Verifica la búsqueda por fragmento del código de historia clínica."""
    dao = BusquedaDAO()
    resultados, total = dao.buscar_por_num_historia("03-77")

    assert total == 1
    assert len(resultados) == 1
    assert resultados[0].num_historia == "03-77-34"


def test_paginacion_limite_y_offset(paciente_con_tarjeta, patch_conexion):
    """Verifica la paginación con Late Join: limit, offset y consistencia entre páginas."""
    # Crear 3 pacientes adicionales para tener 4 en total
    _crear_paciente_con_tarjeta(patch_conexion, "20000001", "Ana", "Alvarez", "11-11-11")
    _crear_paciente_con_tarjeta(patch_conexion, "20000002", "Bernardo", "Blanco", "22-22-22")
    _crear_paciente_con_tarjeta(patch_conexion, "20000003", "Camilo", "Castro", "44-44-44")

    dao = BusquedaDAO()

    # Página 1: primeros 2
    pag1, total1 = dao.obtener_todos(limit=2, offset=0)
    assert total1 == 4
    assert len(pag1) == 2

    # Página 2: siguientes 2
    pag2, total2 = dao.obtener_todos(limit=2, offset=2)
    assert total2 == 4
    assert len(pag2) == 2

    # Comprobar que los registros de cada página sean distintos
    ids_pag1 = {p.id_paciente for p in pag1}
    ids_pag2 = {p.id_paciente for p in pag2}
    assert ids_pag1.isdisjoint(ids_pag2)


def test_busqueda_sin_resultados(paciente_con_tarjeta):
    """Verifica que una búsqueda sin coincidencias retorne lista vacía y total 0."""
    dao = BusquedaDAO()
    resultados, total = dao.buscar_por_cedula("ZZZZZ")

    assert total == 0
    assert len(resultados) == 0


def test_buscar_multicriterio_vacio(paciente_con_tarjeta):
    """Verifica que buscar_multicriterio sin filtros invoque obtener_todos()."""
    dao = BusquedaDAO()
    resultados, total = dao.buscar_multicriterio({})

    assert total == 1
    assert len(resultados) == 1


def test_buscar_multicriterio_filtros_vacios(paciente_con_tarjeta):
    """Verifica que un diccionario con filtros nulos o vacíos se degrade a obtener_todos()."""
    dao = BusquedaDAO()
    filtros = {
        "cedula": "",
        "nombre": "   ",
        "apellido": None,
        "lugar_nacimiento": "",
    }
    resultados, total = dao.buscar_multicriterio(filtros)

    assert total == 1
    assert len(resultados) == 1


def test_buscar_multicriterio_fts_combinado(paciente_con_tarjeta, patch_conexion):
    """Verifica la búsqueda combinada con FTS5 (cédula, nombre y apellido simultáneos)."""
    dao = BusquedaDAO()
    filtros = {
        "cedula": "12345",
        "nombre": "María",
        "apellido": "González",
    }
    resultados, total = dao.buscar_multicriterio(filtros)

    assert total == 1
    assert len(resultados) == 1
    assert resultados[0].id_paciente == paciente_con_tarjeta["id"]


def test_buscar_multicriterio_solo_lugar(paciente_con_tarjeta):
    """Verifica la rama multicriterio sin FTS (usando únicamente lugar_nacimiento)."""
    dao = BusquedaDAO()
    filtros = {"lugar_nacimiento": "Turén"}
    resultados, total = dao.buscar_multicriterio(filtros)

    assert total == 1
    assert len(resultados) == 1
    assert resultados[0].lugar_nacimiento == "Turén"


def test_buscar_multicriterio_fecha_completa(paciente_con_tarjeta):
    """Verifica la rama multicriterio con filtro de fecha completa."""
    dao = BusquedaDAO()
    filtros = {"fecha_nacimiento": "15/05/1990"}
    resultados, total = dao.buscar_multicriterio(filtros)

    assert total == 1
    assert len(resultados) == 1


def test_buscar_multicriterio_fecha_partes(paciente_con_tarjeta):
    """Verifica la búsqueda usando fecha_nacimiento_partes (día, mes, año separados)."""
    dao = BusquedaDAO()

    # Coincidencia con día, mes y año válidos
    filtros = {
        "fecha_nacimiento_partes": ("15", "5", "1990")
    }
    resultados, total = dao.buscar_multicriterio(filtros)
    assert total == 1
    assert len(resultados) == 1

    # Solo mes
    filtros_mes = {
        "fecha_nacimiento_partes": ("", "05", "")
    }
    resultados_mes, total_mes = dao.buscar_multicriterio(filtros_mes)
    assert total_mes == 1

    # Valores inválidos (no numéricos) son ignorados sin fallar
    filtros_invalidos = {
        "fecha_nacimiento_partes": ("dia_invalido", "mes_invalido", "anio_invalido")
    }
    _, total_inv = dao.buscar_multicriterio(filtros_invalidos)
    assert total_inv == 1  # Se degrada a todos
