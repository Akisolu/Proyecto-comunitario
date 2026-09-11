"""
Pruebas unitarias para IngresoDAO (Capa de Acceso a Datos de Ingresos Hospitalarios).

Verifica el registro de ingresos en servicios, la restricción de unicidad de paciente
(evitar doble ingreso simultáneo), conteo por servicio, egreso físico (DELETE),
consulta de ingreso activo y búsqueda de pacientes disponibles para ingreso.
"""

import pytest
from dao.ingreso import IngresoDAO
from models.servicio import IngresoCreate, Ingreso, IngresoDetalle


def test_crear_ingreso_exitoso(paciente_con_tarjeta):
    """Verifica que un paciente con tarjeta pueda ingresar a un servicio hospitalario."""
    dao = IngresoDAO()
    ingreso = IngresoCreate(
        id_paciente=paciente_con_tarjeta["id"],
        id_servicio=1,
        fecha_ingreso="10/09/2026",
    )
    id_ingreso = dao.crear(ingreso)
    assert id_ingreso > 0

    registro = dao.obtener_ingreso_paciente(paciente_con_tarjeta["id"])
    assert registro is not None
    assert registro.id == id_ingreso
    assert registro.id_servicio == 1


def test_rechazo_doble_ingreso(paciente_con_tarjeta):
    """Verifica que un paciente no pueda ser ingresado dos veces simultáneamente."""
    dao = IngresoDAO()
    i1 = IngresoCreate(
        id_paciente=paciente_con_tarjeta["id"],
        id_servicio=1,
        fecha_ingreso="10/09/2026",
    )
    id1 = dao.crear(i1)
    assert id1 > 0

    # Intentar ingresar al mismo paciente en otro servicio
    i2 = IngresoCreate(
        id_paciente=paciente_con_tarjeta["id"],
        id_servicio=2,
        fecha_ingreso="11/09/2026",
    )
    id2 = dao.crear(i2)
    assert id2 == -1


def test_contar_por_servicio(paciente_con_tarjeta):
    """Verifica el conteo de pacientes ingresados en un servicio hospitalario."""
    dao = IngresoDAO()
    dao.crear(
        IngresoCreate(
            id_paciente=paciente_con_tarjeta["id"],
            id_servicio=1,
            fecha_ingreso="10/09/2026",
        )
    )

    assert dao.contar_por_servicio(1) == 1
    assert dao.contar_por_servicio(2) == 0


def test_contar_por_servicio_vacio(patch_conexion):
    """Verifica que el conteo en un servicio sin ingresos retorne 0."""
    dao = IngresoDAO()
    assert dao.contar_por_servicio(1) == 0


def test_eliminar_ingreso(paciente_con_tarjeta):
    """Verifica el egreso/alta de un paciente eliminando el registro de ingreso por ID."""
    dao = IngresoDAO()
    id_ingreso = dao.crear(
        IngresoCreate(
            id_paciente=paciente_con_tarjeta["id"],
            id_servicio=1,
            fecha_ingreso="10/09/2026",
        )
    )
    assert dao.contar_por_servicio(1) == 1

    exito = dao.eliminar(id_ingreso)
    assert exito is True
    assert dao.contar_por_servicio(1) == 0


def test_eliminar_por_paciente(paciente_con_tarjeta):
    """Verifica el egreso de un paciente liberando su ingreso mediante el id_paciente."""
    dao = IngresoDAO()
    dao.crear(
        IngresoCreate(
            id_paciente=paciente_con_tarjeta["id"],
            id_servicio=1,
            fecha_ingreso="10/09/2026",
        )
    )
    assert dao.contar_por_servicio(1) == 1

    exito = dao.eliminar_por_paciente(paciente_con_tarjeta["id"])
    assert exito is True
    assert dao.contar_por_servicio(1) == 0


def test_obtener_ingreso_paciente(paciente_con_tarjeta):
    """Verifica la recuperación del modelo Ingreso para un paciente ingresado."""
    dao = IngresoDAO()
    id_ingreso = dao.crear(
        IngresoCreate(
            id_paciente=paciente_con_tarjeta["id"],
            id_servicio=1,
            fecha_ingreso="10/09/2026",
        )
    )

    ingreso = dao.obtener_ingreso_paciente(paciente_con_tarjeta["id"])
    assert ingreso is not None
    assert isinstance(ingreso, Ingreso)
    assert ingreso.id == id_ingreso
    assert ingreso.id_paciente == paciente_con_tarjeta["id"]
    assert ingreso.id_servicio == 1


def test_obtener_ingreso_paciente_sin_ingreso(paciente_con_tarjeta):
    """Verifica que obtener_ingreso_paciente retorne None si el paciente no está hospitalizado."""
    dao = IngresoDAO()
    assert dao.obtener_ingreso_paciente(paciente_con_tarjeta["id"]) is None


def test_buscar_pacientes_disponibles(paciente_con_tarjeta):
    """Verifica que solo pacientes con tarjeta y NO ingresados aparezcan disponibles."""
    dao = IngresoDAO()

    # Antes del ingreso: el paciente con tarjeta debe encontrarse disponible
    disponibles_antes = dao.buscar_pacientes_disponibles(paciente_con_tarjeta["nombre1"])
    assert len(disponibles_antes) == 1
    assert disponibles_antes[0]["id"] == paciente_con_tarjeta["id"]
    assert disponibles_antes[0]["num_historia"] == paciente_con_tarjeta["num_historia"]

    # Realizar ingreso en el servicio 1
    dao.crear(
        IngresoCreate(
            id_paciente=paciente_con_tarjeta["id"],
            id_servicio=1,
            fecha_ingreso="10/09/2026",
        )
    )

    # Después del ingreso: ya no debe aparecer en la búsqueda de disponibles
    disponibles_despues = dao.buscar_pacientes_disponibles(paciente_con_tarjeta["nombre1"])
    assert len(disponibles_despues) == 0
