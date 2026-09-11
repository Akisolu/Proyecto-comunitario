"""Pruebas unitarias para el controlador de pacientes (PacienteController).

Módulo bajo prueba: controllers.paciente_controller
Valida:
    - Registro de pacientes con datos válidos e inválidos
    - Detección de cédulas duplicadas tanto en registro como en actualización
    - Registro conjunto de paciente y tarjeta con derivación automática de color
    - Consulta de pacientes por ID y por cédula
    - Listado de pacientes activos
    - Actualización de datos de pacientes existentes
    - Borrado lógico (desactivación) de pacientes
"""

import pytest
from controllers.paciente_controller import PacienteController
from models.paciente import Paciente


def _datos_paciente(cedula="V-11111111", nombre1="Ana", apellido1="Martínez"):
    """Función auxiliar para generar diccionarios de prueba de pacientes."""
    return {
        "cedula": cedula,
        "nombre1": nombre1,
        "nombre2": "",
        "apellido1": apellido1,
        "apellido2": "",
        "fecha_nacimiento": "01/01/1990",
        "lugar_nacimiento": "Caracas",
        "estado_vital": 1,
    }


def test_registrar_paciente_exitoso(patch_conexion):
    """Verifica el registro exitoso de un paciente con datos válidos."""
    controller = PacienteController()
    datos = _datos_paciente()

    exito, mensaje, id_paciente = controller.registrar_paciente(datos)

    assert exito is True
    assert "exitosamente" in mensaje.lower()
    assert id_paciente is not None
    assert id_paciente > 0


def test_registrar_paciente_datos_invalidos(patch_conexion):
    """Verifica que el registro falle cuando los datos no superan la validación Pydantic."""
    controller = PacienteController()
    datos = _datos_paciente(nombre1="")  # nombre1 es obligatorio

    exito, mensaje, id_paciente = controller.registrar_paciente(datos)

    assert exito is False
    assert "errores de validacion" in mensaje.lower()
    assert id_paciente is None


def test_registrar_paciente_cedula_duplicada(patch_conexion):
    """Verifica que no se permita registrar dos pacientes con la misma cédula."""
    controller = PacienteController()
    datos1 = _datos_paciente(cedula="V-12345678")
    datos2 = _datos_paciente(cedula="V-12345678", nombre1="Pedro")

    exito1, _, id1 = controller.registrar_paciente(datos1)
    assert exito1 is True
    assert id1 is not None

    exito2, mensaje2, id2 = controller.registrar_paciente(datos2)
    assert exito2 is False
    assert "ya existe un paciente con la cédula" in mensaje2.lower()
    assert id2 is None


def test_registrar_paciente_con_tarjeta_exitoso(patch_conexion):
    """Verifica el registro simultáneo de paciente y tarjeta con resolución de color."""
    controller = PacienteController()
    datos = _datos_paciente(cedula="V-22222222")

    # 01-02-30 -> decena 3 -> Naranja
    exito, mensaje = controller.registrar_paciente_con_tarjeta(datos, "01-02-30")

    assert exito is True
    assert "Color: Naranja" in mensaje


def test_registrar_paciente_con_tarjeta_formato_invalido(patch_conexion):
    """Verifica que falle el registro conjunto si el número de historia tiene formato inválido."""
    controller = PacienteController()
    datos = _datos_paciente(cedula="V-33333333")

    exito, mensaje = controller.registrar_paciente_con_tarjeta(datos, "invalid")

    assert exito is False
    assert "formato de numero de historia invalido" in mensaje.lower()


def test_registrar_paciente_con_tarjeta_duplicada(patch_conexion):
    """Verifica que falle si se intenta asignar un número de historia que ya existe."""
    controller = PacienteController()
    datos1 = _datos_paciente(cedula="V-44444441")
    datos2 = _datos_paciente(cedula="V-44444442")

    exito1, _ = controller.registrar_paciente_con_tarjeta(datos1, "01-02-30")
    assert exito1 is True

    exito2, mensaje2 = controller.registrar_paciente_con_tarjeta(datos2, "01-02-30")
    assert exito2 is False
    assert "duplicado" in mensaje2.lower()


def test_obtener_paciente_existente(paciente_semilla):
    """Verifica la recuperación de un paciente existente por su ID."""
    controller = PacienteController()
    id_paciente = paciente_semilla["id"]

    exito, paciente = controller.obtener_paciente(id_paciente)

    assert exito is True
    assert isinstance(paciente, Paciente)
    assert paciente.id == id_paciente
    assert paciente.cedula == paciente_semilla["cedula"]
    assert paciente.nombre1 == paciente_semilla["nombre1"]

    # Verificar también obtención directa por ID
    directo = controller.obtener_paciente_por_id(id_paciente)
    assert directo is not None
    assert directo.id == id_paciente


def test_obtener_paciente_inexistente(patch_conexion):
    """Verifica que consultar un paciente que no existe retorne False."""
    controller = PacienteController()

    exito, mensaje = controller.obtener_paciente(99999)

    assert exito is False
    assert "no encontrado o inactivo" in mensaje.lower()
    assert controller.obtener_paciente_por_id(99999) is None


def test_listar_pacientes(patch_conexion):
    """Verifica que listar_pacientes devuelva todos los pacientes activos."""
    controller = PacienteController()

    controller.registrar_paciente(_datos_paciente(cedula="V-55555551", nombre1="Uno"))
    controller.registrar_paciente(_datos_paciente(cedula="V-55555552", nombre1="Dos"))

    pacientes = controller.listar_pacientes()
    assert len(pacientes) == 2
    assert all(isinstance(p, Paciente) for p in pacientes)


def test_actualizar_paciente(paciente_semilla):
    """Verifica la actualización correcta de los datos de un paciente."""
    controller = PacienteController()
    id_paciente = paciente_semilla["id"]

    datos_actualizados = _datos_paciente(
        cedula=paciente_semilla["cedula"],
        nombre1="Carmen",
        apellido1="González",
    )

    exito, mensaje = controller.actualizar_paciente(id_paciente, datos_actualizados)

    assert exito is True
    assert "actualizado exitosamente" in mensaje.lower()

    paciente = controller.obtener_paciente_por_id(id_paciente)
    assert paciente is not None
    assert paciente.nombre1 == "Carmen"


def test_actualizar_paciente_cedula_duplicada(patch_conexion):
    """Verifica que no se pueda actualizar la cédula a una que ya pertenece a otro paciente."""
    controller = PacienteController()

    _, _, id1 = controller.registrar_paciente(_datos_paciente(cedula="V-66666661", nombre1="P1"))
    _, _, id2 = controller.registrar_paciente(_datos_paciente(cedula="V-66666662", nombre1="P2"))

    # Intentar asignar la cédula del paciente 1 al paciente 2
    datos_duplicados = _datos_paciente(cedula="V-66666661", nombre1="P2_modificado")
    exito, mensaje = controller.actualizar_paciente(id2, datos_duplicados)

    assert exito is False
    assert "ya existe otro paciente" in mensaje.lower()


def test_eliminar_paciente(paciente_semilla):
    """Verifica el borrado lógico (desactivación) de un paciente."""
    controller = PacienteController()
    id_paciente = paciente_semilla["id"]

    exito, mensaje = controller.eliminar_paciente(id_paciente)

    assert exito is True
    assert "desactivado exitosamente" in mensaje.lower()

    # El paciente ya no debe ser encontrado por los métodos activos
    exito_obtener, _ = controller.obtener_paciente(id_paciente)
    assert exito_obtener is False
    assert controller.obtener_paciente_por_id(id_paciente) is None
