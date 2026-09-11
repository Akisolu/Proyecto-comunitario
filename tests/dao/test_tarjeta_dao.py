"""
Pruebas unitarias para TarjetaDAO (Capa de Acceso a Datos de Tarjetas Índice).

Verifica la creación, unicidad de número de historia, consultas por paciente y número,
detección de tarjetas existentes, obtención del último número correlativo y borrado lógico.
"""

import pytest
from dao.tarjeta import TarjetaDAO
from dao.color import ColorDAO
from dao.paciente import PacienteDAO
from models.tarjeta import TarjetaCreate, Tarjeta
from models.paciente import PacienteCreate


def test_crear_tarjeta_exitosa(paciente_semilla):
    """Verifica que se pueda registrar una tarjeta válida asociada a un paciente."""
    tarjeta_dao = TarjetaDAO()
    color_dao = ColorDAO()

    color = color_dao.obtener_por_valor("Naranja")
    assert color is not None

    tarjeta = TarjetaCreate(
        num_historia="03-77-34",
        id_paciente=paciente_semilla["id"],
        id_color=color.id,
    )
    id_tarjeta = tarjeta_dao.crear(tarjeta)
    assert id_tarjeta > 0

    tarjeta_guardada = tarjeta_dao.obtener_por_id(id_tarjeta)
    assert tarjeta_guardada is not None
    assert tarjeta_guardada.num_historia == "03-77-34"
    assert tarjeta_guardada.id_paciente == paciente_semilla["id"]
    assert tarjeta_guardada.id_color == color.id


def test_rechazo_num_historia_duplicado(paciente_semilla, patch_conexion):
    """Verifica que intentar asignar un número de historia ya existente retorne -1."""
    tarjeta_dao = TarjetaDAO()
    color_dao = ColorDAO()
    paciente_dao = PacienteDAO()

    color = color_dao.obtener_por_valor("Naranja")
    assert color is not None

    # Primera tarjeta asignada al paciente de la semilla
    t1 = TarjetaCreate(
        num_historia="03-77-34",
        id_paciente=paciente_semilla["id"],
        id_color=color.id,
    )
    id1 = tarjeta_dao.crear(t1)
    assert id1 > 0

    # Crear segundo paciente para intentar asignarle el mismo num_historia
    p2_id = paciente_dao.crear(
        PacienteCreate(
            cedula="V-87654321",
            nombre1="Pedro",
            apellido1="Pérez",
            fecha_nacimiento="20/01/1980",
            lugar_nacimiento="Acarigua",
            estado_vital=1,
        )
    )
    assert p2_id > 0

    t2 = TarjetaCreate(
        num_historia="03-77-34",
        id_paciente=p2_id,
        id_color=color.id,
    )
    id2 = tarjeta_dao.crear(t2)
    assert id2 == -1


def test_obtener_por_paciente(paciente_con_tarjeta):
    """Verifica la recuperación de la tarjeta asociada al ID de un paciente."""
    tarjeta_dao = TarjetaDAO()
    tarjeta = tarjeta_dao.obtener_por_paciente(paciente_con_tarjeta["id"])

    assert tarjeta is not None
    assert isinstance(tarjeta, Tarjeta)
    assert tarjeta.id == paciente_con_tarjeta["id_tarjeta"]
    assert tarjeta.num_historia == paciente_con_tarjeta["num_historia"]
    assert tarjeta.id_paciente == paciente_con_tarjeta["id"]


def test_obtener_por_num_historia(paciente_con_tarjeta):
    """Verifica la búsqueda de tarjeta a partir del código del número de historia."""
    tarjeta_dao = TarjetaDAO()
    tarjeta = tarjeta_dao.obtener_por_num_historia(paciente_con_tarjeta["num_historia"])

    assert tarjeta is not None
    assert tarjeta.id == paciente_con_tarjeta["id_tarjeta"]
    assert tarjeta.id_paciente == paciente_con_tarjeta["id"]


def test_paciente_tiene_tarjeta(paciente_con_tarjeta):
    """Verifica que paciente_tiene_tarjeta devuelva True si el paciente posee tarjeta activa."""
    tarjeta_dao = TarjetaDAO()
    assert tarjeta_dao.paciente_tiene_tarjeta(paciente_con_tarjeta["id"]) is True


def test_paciente_sin_tarjeta(paciente_semilla):
    """Verifica que paciente_tiene_tarjeta devuelva False si el paciente aún no tiene tarjeta."""
    tarjeta_dao = TarjetaDAO()
    assert tarjeta_dao.paciente_tiene_tarjeta(paciente_semilla["id"]) is False


def test_obtener_ultimo_num_historia(paciente_con_tarjeta):
    """Verifica la obtención del último número de historia registrado."""
    tarjeta_dao = TarjetaDAO()
    ultimo = tarjeta_dao.obtener_ultimo_num_historia()
    assert ultimo == "03-77-34"


def test_obtener_ultimo_num_historia_vacio(patch_conexion):
    """Verifica que obtener_ultimo_num_historia retorne None cuando no hay tarjetas registradas."""
    tarjeta_dao = TarjetaDAO()
    assert tarjeta_dao.obtener_ultimo_num_historia() is None


def test_soft_delete_tarjeta(paciente_con_tarjeta):
    """Verifica el borrado lógico de una tarjeta índice."""
    tarjeta_dao = TarjetaDAO()
    exito = tarjeta_dao.soft_delete(paciente_con_tarjeta["id_tarjeta"])
    assert exito is True

    # La tarjeta ya no debe figurar activa para el paciente
    assert tarjeta_dao.obtener_por_paciente(paciente_con_tarjeta["id"]) is None
    assert tarjeta_dao.obtener_por_id(paciente_con_tarjeta["id_tarjeta"]) is None
