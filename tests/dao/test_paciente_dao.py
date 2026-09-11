"""
Pruebas unitarias para PacienteDAO (Capa de Acceso a Datos de Pacientes).

Verifica la persistencia, restricciones de unicidad, manejo de pacientes sin cédula,
consultas por ID y cédula, actualización y borrado lógico (soft delete).
"""

import pytest
from dao.paciente import PacienteDAO
from models.paciente import PacienteCreate, Paciente


def test_crear_paciente_exitoso(patch_conexion):
    """Verifica que un paciente válido se registre correctamente retornando un ID positivo."""
    dao = PacienteDAO()
    datos = PacienteCreate(
        cedula="V-12345678",
        nombre1="María",
        apellido1="González",
        fecha_nacimiento="15/05/1990",
        lugar_nacimiento="Turén",
        estado_vital=1,
    )
    nuevo_id = dao.crear(datos)
    assert nuevo_id > 0

    paciente_guardado = dao.obtener_por_id(nuevo_id)
    assert paciente_guardado is not None
    assert paciente_guardado.cedula == "V-12345678"
    assert paciente_guardado.nombre1 == "María"
    assert paciente_guardado.apellido1 == "González"


def test_crear_multiples_sin_cedula(patch_conexion):
    """Verifica que múltiples pacientes sin cédula ('S/C') puedan registrarse sin violar UNIQUE."""
    dao = PacienteDAO()
    p1 = PacienteCreate(
        cedula="S/C",
        nombre1="Recién",
        apellido1="NacidoUno",
        fecha_nacimiento="01/01/2026",
        lugar_nacimiento="Turén",
        estado_vital=1,
    )
    p2 = PacienteCreate(
        cedula="S/C",
        nombre1="Recién",
        apellido1="NacidoDos",
        fecha_nacimiento="02/01/2026",
        lugar_nacimiento="Turén",
        estado_vital=1,
    )

    id1 = dao.crear(p1)
    id2 = dao.crear(p2)

    assert id1 > 0
    assert id2 > 0
    assert id1 != id2

    # Comprobar que al recuperarlos se representen como 'S/C'
    pac1 = dao.obtener_por_id(id1)
    pac2 = dao.obtener_por_id(id2)
    assert pac1 is not None and pac1.cedula == "S/C"
    assert pac2 is not None and pac2.cedula == "S/C"


def test_rechazo_cedula_duplicada(patch_conexion):
    """Verifica que intentar registrar dos pacientes con la misma cédula retorne -1 por colisión UNIQUE."""
    dao = PacienteDAO()
    p1 = PacienteCreate(
        cedula="V-20111222",
        nombre1="Carlos",
        apellido1="Rivas",
        fecha_nacimiento="10/10/1985",
        lugar_nacimiento="Caracas",
        estado_vital=1,
    )
    p2 = PacienteCreate(
        cedula="V-20111222",
        nombre1="José",
        apellido1="Rivas",
        fecha_nacimiento="11/11/1986",
        lugar_nacimiento="Caracas",
        estado_vital=1,
    )

    id1 = dao.crear(p1)
    assert id1 > 0

    id2 = dao.crear(p2)
    assert id2 == -1


def test_obtener_por_id(paciente_semilla):
    """Verifica que obtener_por_id devuelva el paciente correcto con sus campos mapeados."""
    dao = PacienteDAO()
    paciente = dao.obtener_por_id(paciente_semilla["id"])

    assert paciente is not None
    assert isinstance(paciente, Paciente)
    assert paciente.id == paciente_semilla["id"]
    assert paciente.cedula == paciente_semilla["cedula"]
    assert paciente.nombre1 == paciente_semilla["nombre1"]
    assert paciente.apellido1 == paciente_semilla["apellido1"]
    assert paciente.fecha_nacimiento == paciente_semilla["fecha_nacimiento"]


def test_obtener_por_id_inexistente(patch_conexion):
    """Verifica que obtener_por_id retorne None al consultar un ID que no existe."""
    dao = PacienteDAO()
    resultado = dao.obtener_por_id(99999)
    assert resultado is None


def test_obtener_por_cedula(paciente_semilla):
    """Verifica que obtener_por_cedula retorne el paciente correspondiente a la cédula consultada."""
    dao = PacienteDAO()
    paciente = dao.obtener_por_cedula(paciente_semilla["cedula"])

    assert paciente is not None
    assert paciente.id == paciente_semilla["id"]
    assert paciente.cedula == paciente_semilla["cedula"]
    assert paciente.nombre1 == paciente_semilla["nombre1"]


def test_obtener_todos(patch_conexion):
    """Verifica que obtener_todos retorne la lista completa de pacientes activos."""
    dao = PacienteDAO()
    for i in range(3):
        dao.crear(
            PacienteCreate(
                cedula=f"V-3000000{i}",
                nombre1=f"Paciente{i}",
                apellido1="Prueba",
                fecha_nacimiento="01/01/1995",
                lugar_nacimiento="Turén",
                estado_vital=1,
            )
        )

    todos = dao.obtener_todos()
    assert len(todos) == 3
    assert all(isinstance(p, Paciente) for p in todos)


def test_actualizar_paciente(paciente_semilla):
    """Verifica la actualización de datos de un paciente existente."""
    dao = PacienteDAO()
    datos_actualizados = PacienteCreate(
        cedula=paciente_semilla["cedula"],
        nombre1="Carmen",
        nombre2="Elena",
        apellido1="González",
        apellido2="López",
        fecha_nacimiento="15/05/1990",
        lugar_nacimiento="Turén",
        estado_vital=1,
    )

    exito = dao.actualizar(paciente_semilla["id"], datos_actualizados)
    assert exito is True

    paciente_recuperado = dao.obtener_por_id(paciente_semilla["id"])
    assert paciente_recuperado is not None
    assert paciente_recuperado.nombre1 == "Carmen"


def test_soft_delete(paciente_semilla):
    """Verifica que el borrado lógico desactive el paciente para consultas ordinarias."""
    dao = PacienteDAO()
    exito = dao.soft_delete(paciente_semilla["id"])
    assert exito is True

    # El paciente desactivado no debe recuperarse por ID
    assert dao.obtener_por_id(paciente_semilla["id"]) is None

    # Tampoco debe figurar en la lista de todos los pacientes activos
    assert len(dao.obtener_todos()) == 0


def test_soft_delete_inexistente(patch_conexion):
    """Verifica que intentar desactivar un paciente que no existe retorne False."""
    dao = PacienteDAO()
    assert dao.soft_delete(99999) is False
