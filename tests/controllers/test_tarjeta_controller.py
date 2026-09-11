"""Pruebas unitarias para el controlador de tarjetas (TarjetaController).

Módulo bajo prueba: controllers.tarjeta_controller
Valida:
    - Creación de tarjetas con auto-derivación cromática según la decena del último par
    - Validaciones de formato (XX-XX-XX), duplicidad y asignación única por paciente
    - Actualización de número de historia y recálculo dinámico del color
    - Consulta de tarjeta por paciente y listado general de tarjetas activas
    - Eliminación lógica (soft delete) de tarjetas
    - Generación secuencial del siguiente número de historia clínica y desbordamientos
"""

import pytest
from controllers.tarjeta_controller import TarjetaController
from dao.paciente import PacienteDAO
from dao.tarjeta import TarjetaDAO
from dao.color import ColorDAO
from models.paciente import PacienteCreate
from models.tarjeta import TarjetaCreate, Tarjeta


def test_crear_tarjeta_exitosa(paciente_semilla):
    """Verifica la creación exitosa de una tarjeta asignando el color correspondiente."""
    controller = TarjetaController()
    id_paciente = paciente_semilla["id"]

    # 01-02-30 -> decena 3 -> Naranja
    exito, mensaje = controller.crear_tarjeta(id_paciente, "01-02-30")

    assert exito is True
    assert "Naranja" in mensaje

    tarjeta = controller.obtener_tarjeta_paciente(id_paciente)
    assert tarjeta is not None
    assert tarjeta.num_historia == "01-02-30"


def test_crear_tarjeta_formato_invalido(paciente_semilla):
    """Verifica que falle la creación si el formato del número de historia no es XX-XX-XX."""
    controller = TarjetaController()
    id_paciente = paciente_semilla["id"]

    exito, mensaje = controller.crear_tarjeta(id_paciente, "invalid")

    assert exito is False
    assert "formato de numero de historia invalido" in mensaje.lower()


def test_crear_tarjeta_paciente_ya_tiene(paciente_con_tarjeta):
    """Verifica que un paciente con tarjeta activa no pueda tener otra tarjeta asignada."""
    controller = TarjetaController()
    id_paciente = paciente_con_tarjeta["id"]

    exito, mensaje = controller.crear_tarjeta(id_paciente, "01-02-30")

    assert exito is False
    assert "ya tiene una tarjeta activa" in mensaje.lower()


def test_crear_tarjeta_num_historia_duplicado(paciente_con_tarjeta, patch_conexion):
    """Verifica que no se pueda asignar un número de historia ya registrado a otro paciente."""
    controller = TarjetaController()
    paciente_dao = PacienteDAO()

    # Crear un segundo paciente
    segundo_paciente = PacienteCreate(
        cedula="V-88888888",
        nombre1="Pedro",
        apellido1="Ramírez",
        fecha_nacimiento="1988-08-08",
        lugar_nacimiento="Valencia",
        estado_vital=1,
    )
    id_segundo = paciente_dao.crear(segundo_paciente)

    # Intentar usar el mismo num_historia que paciente_con_tarjeta ("03-77-34")
    exito, mensaje = controller.crear_tarjeta(id_segundo, paciente_con_tarjeta["num_historia"])

    assert exito is False
    assert "ya existe una tarjeta con ese numero de historia" in mensaje.lower()


def test_actualizar_tarjeta_exitosa(paciente_con_tarjeta):
    """Verifica la actualización del número de historia y recálculo automático del color."""
    controller = TarjetaController()
    id_tarjeta = paciente_con_tarjeta["id_tarjeta"]

    # 05-10-50 -> decena 5 -> Rosa
    exito, mensaje = controller.actualizar_tarjeta(id_tarjeta, "05-10-50")

    assert exito is True
    assert "Rosa" in mensaje

    tarjeta = controller.obtener_tarjeta_paciente(paciente_con_tarjeta["id"])
    assert tarjeta is not None
    assert tarjeta.num_historia == "05-10-50"


def test_actualizar_tarjeta_inexistente(patch_conexion):
    """Verifica el error al intentar actualizar una tarjeta que no existe."""
    controller = TarjetaController()

    exito, mensaje = controller.actualizar_tarjeta(99999, "05-10-50")

    assert exito is False
    assert "no encontrada o inactiva" in mensaje.lower()


def test_actualizar_tarjeta_formato_invalido(paciente_con_tarjeta):
    """Verifica el error al intentar actualizar con un número de historia inválido."""
    controller = TarjetaController()
    id_tarjeta = paciente_con_tarjeta["id_tarjeta"]

    exito, mensaje = controller.actualizar_tarjeta(id_tarjeta, "99-bad")

    assert exito is False
    assert "formato invalido" in mensaje.lower()


def test_obtener_tarjeta_paciente(paciente_con_tarjeta):
    """Verifica la obtención de la tarjeta activa de un paciente."""
    controller = TarjetaController()

    tarjeta = controller.obtener_tarjeta_paciente(paciente_con_tarjeta["id"])

    assert tarjeta is not None
    assert isinstance(tarjeta, Tarjeta)
    assert tarjeta.num_historia == paciente_con_tarjeta["num_historia"]
    assert tarjeta.id_paciente == paciente_con_tarjeta["id"]


def test_obtener_tarjeta_paciente_sin_tarjeta(paciente_semilla):
    """Verifica que un paciente sin tarjeta asignada retorne None."""
    controller = TarjetaController()

    tarjeta = controller.obtener_tarjeta_paciente(paciente_semilla["id"])

    assert tarjeta is None


def test_listar_tarjetas(paciente_con_tarjeta):
    """Verifica que listar_tarjetas retorne la lista de tarjetas activas."""
    controller = TarjetaController()

    tarjetas = controller.listar_tarjetas()

    assert len(tarjetas) >= 1
    assert any(t.id == paciente_con_tarjeta["id_tarjeta"] for t in tarjetas)


def test_eliminar_tarjeta(paciente_con_tarjeta):
    """Verifica la desactivación lógica de una tarjeta."""
    controller = TarjetaController()
    id_tarjeta = paciente_con_tarjeta["id_tarjeta"]

    exito, mensaje = controller.eliminar_tarjeta(id_tarjeta)

    assert exito is True
    assert "desactivada exitosamente" in mensaje.lower()

    # Ya no debe retornar la tarjeta del paciente
    tarjeta = controller.obtener_tarjeta_paciente(paciente_con_tarjeta["id"])
    assert tarjeta is None


def test_generar_siguiente_sin_registros(patch_conexion):
    """Verifica que en una base de datos sin tarjetas se comience con '00-00-01'."""
    controller = TarjetaController()

    siguiente = controller.generar_siguiente_num_historia()

    assert siguiente == "00-00-01"


def test_generar_siguiente_secuencial(paciente_con_tarjeta):
    """Verifica el incremento secuencial del último par ('03-77-34' -> '03-77-35')."""
    controller = TarjetaController()

    siguiente = controller.generar_siguiente_num_historia()

    assert siguiente == "03-77-35"


def test_generar_siguiente_desborde_ultimo_par(patch_conexion, paciente_semilla):
    """Verifica el desbordamiento del último par: '03-77-99' -> '03-78-00'."""
    tarjeta_dao = TarjetaDAO()
    color_dao = ColorDAO()
    color = color_dao.obtener_por_valor("Azul Celeste")  # Decena 9

    tarjeta_dao.crear(
        TarjetaCreate(
            num_historia="03-77-99",
            id_paciente=paciente_semilla["id"],
            id_color=color.id,
        )
    )

    controller = TarjetaController()
    siguiente = controller.generar_siguiente_num_historia()

    assert siguiente == "03-78-00"


def test_generar_siguiente_desborde_medio(patch_conexion, paciente_semilla):
    """Verifica el desbordamiento sucesivo del último y segundo par: '03-99-99' -> '04-00-00'."""
    tarjeta_dao = TarjetaDAO()
    color_dao = ColorDAO()
    color = color_dao.obtener_por_valor("Azul Celeste")  # Decena 9

    tarjeta_dao.crear(
        TarjetaCreate(
            num_historia="03-99-99",
            id_paciente=paciente_semilla["id"],
            id_color=color.id,
        )
    )

    controller = TarjetaController()
    siguiente = controller.generar_siguiente_num_historia()

    assert siguiente == "04-00-00"


def test_generar_siguiente_desborde_completo(patch_conexion, paciente_semilla):
    """Verifica el desbordamiento total de todos los pares: '99-99-99' -> '00-00-00'."""
    tarjeta_dao = TarjetaDAO()
    color_dao = ColorDAO()
    color = color_dao.obtener_por_valor("Azul Celeste")  # Decena 9

    tarjeta_dao.crear(
        TarjetaCreate(
            num_historia="99-99-99",
            id_paciente=paciente_semilla["id"],
            id_color=color.id,
        )
    )

    controller = TarjetaController()
    siguiente = controller.generar_siguiente_num_historia()

    assert siguiente == "00-00-00"
