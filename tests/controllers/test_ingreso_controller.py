"""Pruebas unitarias para el controlador de ingresos (IngresoController).

Módulo bajo prueba: controllers.ingreso_controller
Valida:
    - Listado de servicios hospitalarios inicializados
    - Consulta de resumen por servicio (camas totales, ocupadas, disponibles e ingresos)
    - Consulta de resumen general del hospital
    - Registro de ingresos con validaciones de:
        * Existencia y estado activo del paciente
        * Asignación obligatoria de tarjeta de salud
        * Restricción de ingreso único por paciente
        * Disponibilidad de camas en el servicio seleccionado
        * Campos requeridos (paciente, servicio, fecha)
    - Registro de egresos (dar de alta a pacientes liberando camas)
    - Actualización de capacidad de camas por servicio y restricciones de ocupación
    - Búsqueda de pacientes con tarjeta disponibles para ingreso
"""

import pytest
from controllers.ingreso_controller import IngresoController
from dao.paciente import PacienteDAO
from dao.tarjeta import TarjetaDAO
from dao.color import ColorDAO
from models.paciente import PacienteCreate
from models.tarjeta import TarjetaCreate


def test_listar_servicios(patch_conexion):
    """Verifica que listar_servicios retorne los 4 servicios hospitalarios base."""
    controller = IngresoController()
    servicios = controller.listar_servicios()

    assert len(servicios) == 4
    nombres = [s.nombre for s in servicios]
    assert "Medicina Interna" in nombres
    assert "Pediatria" in nombres
    assert "Cirugia" in nombres
    assert "Obstetricia" in nombres


def test_obtener_resumen_servicio_vacio(patch_conexion):
    """Verifica el resumen de un servicio sin pacientes ingresados."""
    controller = IngresoController()
    resumen = controller.obtener_resumen_servicio(1)

    assert resumen is not None
    assert resumen["total_camas"] == 10
    assert resumen["ocupadas"] == 0
    assert resumen["disponibles"] == 10
    assert resumen["ingresos"] == []


def test_obtener_resumen_servicio_inexistente(patch_conexion):
    """Verifica que consultar un servicio inexistente retorne None."""
    controller = IngresoController()
    resumen = controller.obtener_resumen_servicio(99999)

    assert resumen is None


def test_registrar_ingreso_exitoso(paciente_con_tarjeta):
    """Verifica el ingreso exitoso de un paciente con tarjeta a un servicio con camas."""
    controller = IngresoController()
    datos = {
        "id_paciente": paciente_con_tarjeta["id"],
        "id_servicio": 1,
        "fecha_ingreso": "10/09/2026",
    }

    exito, mensaje = controller.registrar_ingreso(datos)

    assert exito is True
    assert "exitosamente" in mensaje.lower()


def test_registrar_ingreso_sin_tarjeta(paciente_semilla):
    """Verifica que no se permita ingresar a un paciente sin tarjeta de salud asignada."""
    controller = IngresoController()
    datos = {
        "id_paciente": paciente_semilla["id"],
        "id_servicio": 1,
        "fecha_ingreso": "10/09/2026",
    }

    exito, mensaje = controller.registrar_ingreso(datos)

    assert exito is False
    assert "tarjeta" in mensaje.lower()


def test_registrar_ingreso_paciente_ya_ingresado(paciente_con_tarjeta):
    """Verifica que un paciente ya ingresado no pueda tener otro ingreso activo."""
    controller = IngresoController()
    datos = {
        "id_paciente": paciente_con_tarjeta["id"],
        "id_servicio": 1,
        "fecha_ingreso": "10/09/2026",
    }

    exito1, _ = controller.registrar_ingreso(datos)
    assert exito1 is True

    # Intentar ingresar nuevamente
    exito2, mensaje2 = controller.registrar_ingreso(datos)
    assert exito2 is False
    assert "ya está ingresado" in mensaje2.lower()


def test_registrar_ingreso_sin_camas(paciente_con_tarjeta, patch_conexion):
    """Verifica que no se pueda ingresar a un paciente si el servicio no tiene camas disponibles."""
    controller = IngresoController()

    # Ajustar capacidad del servicio 1 a 1 cama
    exito_camas, _ = controller.actualizar_camas_servicio(1, 1)
    assert exito_camas is True

    # Ingresar al primer paciente para ocupar la única cama
    exito1, _ = controller.registrar_ingreso({
        "id_paciente": paciente_con_tarjeta["id"],
        "id_servicio": 1,
        "fecha_ingreso": "10/09/2026",
    })
    assert exito1 is True

    # Crear un segundo paciente con tarjeta
    paciente_dao = PacienteDAO()
    tarjeta_dao = TarjetaDAO()
    color_dao = ColorDAO()

    id_p2 = paciente_dao.crear(
        PacienteCreate(
            cedula="V-77777771",
            nombre1="Carlos",
            apellido1="Paredes",
            fecha_nacimiento="1992-04-12",
            lugar_nacimiento="Valencia",
            estado_vital=1,
        )
    )
    color = color_dao.obtener_por_valor("Verde")
    tarjeta_dao.crear(
        TarjetaCreate(
            num_historia="02-15-20",
            id_paciente=id_p2,
            id_color=color.id,
        )
    )

    # Intentar ingresar al segundo paciente al servicio lleno (1/1)
    exito2, mensaje2 = controller.registrar_ingreso({
        "id_paciente": id_p2,
        "id_servicio": 1,
        "fecha_ingreso": "10/09/2026",
    })

    assert exito2 is False
    assert "no hay camas disponibles" in mensaje2.lower()


def test_registrar_egreso_exitoso(paciente_con_tarjeta):
    """Verifica que registrar el egreso dé de alta al paciente y libere la cama."""
    controller = IngresoController()
    datos = {
        "id_paciente": paciente_con_tarjeta["id"],
        "id_servicio": 1,
        "fecha_ingreso": "10/09/2026",
    }

    controller.registrar_ingreso(datos)

    resumen_antes = controller.obtener_resumen_servicio(1)
    assert resumen_antes["ocupadas"] == 1
    id_ingreso = resumen_antes["ingresos"][0].id

    exito, mensaje = controller.registrar_egreso(id_ingreso)

    assert exito is True
    assert "alta exitosamente" in mensaje.lower()

    resumen_despues = controller.obtener_resumen_servicio(1)
    assert resumen_despues["ocupadas"] == 0
    assert resumen_despues["disponibles"] == resumen_despues["total_camas"]


def test_registrar_egreso_inexistente(patch_conexion):
    """Verifica que el egreso falle cuando el ID de ingreso no existe."""
    controller = IngresoController()

    exito, mensaje = controller.registrar_egreso(99999)

    assert exito is False
    assert "no se encontró" in mensaje.lower()


def test_obtener_resumen_con_ingresos(paciente_con_tarjeta):
    """Verifica que el resumen del servicio refleje correctamente las camas ocupadas y disponibles."""
    controller = IngresoController()
    datos = {
        "id_paciente": paciente_con_tarjeta["id"],
        "id_servicio": 1,
        "fecha_ingreso": "10/09/2026",
    }
    controller.registrar_ingreso(datos)

    resumen = controller.obtener_resumen_servicio(1)

    assert resumen["ocupadas"] == 1
    assert resumen["disponibles"] == 9
    assert len(resumen["ingresos"]) == 1
    assert resumen["ingresos"][0].id_paciente == paciente_con_tarjeta["id"]


def test_actualizar_camas_exitoso(patch_conexion):
    """Verifica la actualización de la capacidad total de camas de un servicio."""
    controller = IngresoController()

    exito, mensaje = controller.actualizar_camas_servicio(1, 15)

    assert exito is True
    assert "15 camas" in mensaje

    resumen = controller.obtener_resumen_servicio(1)
    assert resumen["total_camas"] == 15
    assert resumen["disponibles"] == 15


def test_actualizar_camas_menor_que_ocupadas(paciente_con_tarjeta):
    """Verifica que no se pueda reducir la capacidad por debajo del número de camas ocupadas.
    
    Para activar la regla (total_camas < ocupadas) sin activar antes (total_camas < 1),
    se ocupan 2 camas y se intenta reducir la capacidad a 1 cama.
    """
    controller = IngresoController()
    id_paciente1 = paciente_con_tarjeta["id"]

    # Ingresar el primer paciente
    controller.registrar_ingreso({
        "id_paciente": id_paciente1,
        "id_servicio": 1,
        "fecha_ingreso": "10/09/2026",
    })

    # Crear e ingresar un segundo paciente
    paciente_dao = PacienteDAO()
    tarjeta_dao = TarjetaDAO()
    color_dao = ColorDAO()

    id_p2 = paciente_dao.crear(
        PacienteCreate(
            cedula="V-66666663",
            nombre1="Elena",
            apellido1="Sucre",
            fecha_nacimiento="1995-11-20",
            lugar_nacimiento="Barquisimeto",
            estado_vital=1,
        )
    )
    color = color_dao.obtener_por_valor("Rosa")
    tarjeta_dao.crear(
        TarjetaCreate(
            num_historia="05-20-55",
            id_paciente=id_p2,
            id_color=color.id,
        )
    )

    controller.registrar_ingreso({
        "id_paciente": id_p2,
        "id_servicio": 1,
        "fecha_ingreso": "10/09/2026",
    })

    # Ahora hay 2 camas ocupadas. Intentar reducir a 1 cama debe ser rechazado
    exito, mensaje = controller.actualizar_camas_servicio(1, 1)

    assert exito is False
    assert "ocupadas" in mensaje.lower()
    assert "2" in mensaje


def test_actualizar_camas_valor_invalido(patch_conexion):
    """Verifica que no se permita fijar una cantidad de camas menor a 1."""
    controller = IngresoController()

    exito_cero, msg_cero = controller.actualizar_camas_servicio(1, 0)
    assert exito_cero is False
    assert "al menos 1" in msg_cero.lower()

    exito_neg, msg_neg = controller.actualizar_camas_servicio(1, -5)
    assert exito_neg is False
    assert "al menos 1" in msg_neg.lower()


def test_actualizar_camas_servicio_inexistente(patch_conexion):
    """Verifica el error al intentar actualizar camas en un servicio que no existe."""
    controller = IngresoController()

    exito, mensaje = controller.actualizar_camas_servicio(99999, 10)

    assert exito is False
    assert "no se encontró el servicio" in mensaje.lower()


def test_registrar_ingreso_campos_vacios(patch_conexion):
    """Verifica la validación de campos obligatorios al registrar un ingreso."""
    controller = IngresoController()

    # Falta id_paciente
    exito, msg = controller.registrar_ingreso({"id_paciente": None, "id_servicio": 1, "fecha_ingreso": "10/09/2026"})
    assert exito is False
    assert "debe seleccionar" in msg.lower()

    # Falta id_servicio
    exito, msg = controller.registrar_ingreso({"id_paciente": 1, "id_servicio": None, "fecha_ingreso": "10/09/2026"})
    assert exito is False
    assert "debe seleccionar" in msg.lower()

    # Falta fecha_ingreso
    exito, msg = controller.registrar_ingreso({"id_paciente": 1, "id_servicio": 1, "fecha_ingreso": ""})
    assert exito is False
    assert "fecha de ingreso es obligatoria" in msg.lower()


def test_registrar_ingreso_paciente_inexistente(patch_conexion):
    """Verifica el error al intentar registrar ingreso para un ID de paciente inexistente."""
    controller = IngresoController()

    exito, mensaje = controller.registrar_ingreso({
        "id_paciente": 99999,
        "id_servicio": 1,
        "fecha_ingreso": "10/09/2026",
    })

    assert exito is False
    assert "no existe o está inactivo" in mensaje.lower()


def test_obtener_resumen_general(paciente_con_tarjeta):
    """Verifica que el resumen general contemple la ocupación de todos los servicios."""
    controller = IngresoController()
    controller.registrar_ingreso({
        "id_paciente": paciente_con_tarjeta["id"],
        "id_servicio": 1,
        "fecha_ingreso": "10/09/2026",
    })

    resumen = controller.obtener_resumen_general()

    assert len(resumen) == 4
    # El primer servicio (Medicina Interna) debe reflejar 1 ocupada
    assert resumen[0]["servicio"].id == 1
    assert resumen[0]["ocupadas"] == 1
    assert resumen[0]["disponibles"] == resumen[0]["total_camas"] - 1


def test_buscar_pacientes_disponibles(paciente_con_tarjeta):
    """Verifica que solo los pacientes con tarjeta y sin ingreso activo aparezcan disponibles."""
    controller = IngresoController()

    # Antes de ingresar, el paciente con tarjeta está disponible
    disponibles_antes = controller.buscar_pacientes_disponibles("María")
    assert len(disponibles_antes) >= 1
    assert any(p["id"] == paciente_con_tarjeta["id"] for p in disponibles_antes)

    # Ingresar el paciente
    controller.registrar_ingreso({
        "id_paciente": paciente_con_tarjeta["id"],
        "id_servicio": 1,
        "fecha_ingreso": "10/09/2026",
    })

    # Después de ingresar, ya no debe estar disponible
    disponibles_despues = controller.buscar_pacientes_disponibles("María")
    assert not any(p["id"] == paciente_con_tarjeta["id"] for p in disponibles_despues)
