"""
Pruebas unitarias para los modelos Pydantic de la aplicación.

Módulos bajo prueba:
    - models.paciente (PacienteCreate, Paciente)
    - models.tarjeta (TarjetaCreate, Tarjeta)
    - models.usuario (UsuarioCreate, Usuario)
Valida:
    - Validación y normalización de cédula, fecha de nacimiento y campos obligatorios de Paciente
    - Validación del formato de número de historia en Tarjeta
    - Obligatoriedad de campos en Usuario
"""

import pytest
from pydantic import ValidationError

from models.paciente import PacienteCreate
from models.tarjeta import TarjetaCreate
from models.usuario import UsuarioCreate


# ══════════════════════════════════════════════════════════════════
#  PRUEBAS DE PACIENTECREATE
# ══════════════════════════════════════════════════════════════════

def test_paciente_create_valido():
    """Verifica la creación exitosa de un PacienteCreate con todos los campos válidos."""
    datos = {
        "cedula": "V-12345678",
        "nombre1": "María",
        "nombre2": "Elena",
        "apellido1": "González",
        "apellido2": "López",
        "fecha_nacimiento": "15/05/1990",
        "lugar_nacimiento": "Turén",
        "estado_vital": 1,
        "estado": 1,
    }
    paciente = PacienteCreate(**datos)
    assert paciente.cedula == "V-12345678"
    assert paciente.nombre1 == "María"
    assert paciente.nombre2 == "Elena"
    assert paciente.apellido1 == "González"
    assert paciente.apellido2 == "López"
    assert paciente.fecha_nacimiento == "1990-05-15"
    assert paciente.lugar_nacimiento == "Turén"
    assert paciente.estado_vital == 1
    assert paciente.estado == 1


def test_paciente_cedula_sc():
    """Verifica que se acepte 'S/C' (sin cédula) tanto en mayúsculas como en minúsculas."""
    paciente = PacienteCreate(
        cedula="S/C",
        nombre1="Ana",
        apellido1="Pérez",
        fecha_nacimiento="2015-06-10",
        lugar_nacimiento="Caracas",
    )
    assert paciente.cedula == "S/C"

    paciente_min = PacienteCreate(
        cedula="s/c",
        nombre1="Carlos",
        apellido1="Gómez",
        fecha_nacimiento="2018-01-20",
        lugar_nacimiento="Valencia",
    )
    assert paciente_min.cedula == "S/C"


def test_paciente_cedula_vacia():
    """Verifica que una cédula vacía o con espacios se normalice automáticamente a 'S/C'."""
    paciente_vacio = PacienteCreate(
        cedula="",
        nombre1="Luis",
        apellido1="Rodríguez",
        fecha_nacimiento="2010-03-12",
        lugar_nacimiento="Barquisimeto",
    )
    assert paciente_vacio.cedula == "S/C"

    paciente_espacios = PacienteCreate(
        cedula="   ",
        nombre1="Pedro",
        apellido1="Martínez",
        fecha_nacimiento="2012-08-15",
        lugar_nacimiento="Acarigua",
    )
    assert paciente_espacios.cedula == "S/C"


def test_paciente_cedula_ve():
    """Verifica que se acepten cédulas con prefijo venezolano 'V-' y extranjero 'E-'."""
    paciente_v = PacienteCreate(
        cedula="V-12345678",
        nombre1="Rosa",
        apellido1="Hernández",
        fecha_nacimiento="1985-04-20",
        lugar_nacimiento="Maracay",
    )
    assert paciente_v.cedula == "V-12345678"

    paciente_e = PacienteCreate(
        cedula="E-12345678",
        nombre1="John",
        apellido1="Smith",
        fecha_nacimiento="1980-11-05",
        lugar_nacimiento="Londres",
    )
    assert paciente_e.cedula == "E-12345678"

    # En minúscula 'v-' o 'e-' debe normalizarse a mayúscula
    paciente_v_min = PacienteCreate(
        cedula="v-12345678",
        nombre1="Lucía",
        apellido1="Fernández",
        fecha_nacimiento="1992-07-22",
        lugar_nacimiento="Turén",
    )
    assert paciente_v_min.cedula == "V-12345678"


def test_paciente_cedula_invalida():
    """Verifica que números de cédula sin prefijo V-/E- o con formato inválido lancen ValidationError."""
    with pytest.raises(ValidationError):
        PacienteCreate(
            cedula="12345678",
            nombre1="Juan",
            apellido1="Pérez",
            fecha_nacimiento="1990-01-01",
            lugar_nacimiento="Caracas",
        )

    with pytest.raises(ValidationError):
        PacienteCreate(
            cedula="X-12345678",
            nombre1="Juan",
            apellido1="Pérez",
            fecha_nacimiento="1990-01-01",
            lugar_nacimiento="Caracas",
        )

    with pytest.raises(ValidationError):
        PacienteCreate(
            cedula="V-123",  # Menos de 6 dígitos
            nombre1="Juan",
            apellido1="Pérez",
            fecha_nacimiento="1990-01-01",
            lugar_nacimiento="Caracas",
        )


def test_paciente_nombre1_vacio():
    """Verifica que un valor vacío o compuesto únicamente por espacios en nombre1 lance ValidationError."""
    with pytest.raises(ValidationError):
        PacienteCreate(
            nombre1="",
            apellido1="Pérez",
            fecha_nacimiento="1990-01-01",
            lugar_nacimiento="Caracas",
        )

    with pytest.raises(ValidationError):
        PacienteCreate(
            nombre1="   ",
            apellido1="Pérez",
            fecha_nacimiento="1990-01-01",
            lugar_nacimiento="Caracas",
        )


def test_paciente_apellido1_vacio():
    """Verifica que un valor vacío o con espacios en blanco en apellido1 lance ValidationError."""
    with pytest.raises(ValidationError):
        PacienteCreate(
            nombre1="Juan",
            apellido1="",
            fecha_nacimiento="1990-01-01",
            lugar_nacimiento="Caracas",
        )

    with pytest.raises(ValidationError):
        PacienteCreate(
            nombre1="Juan",
            apellido1="   ",
            fecha_nacimiento="1990-01-01",
            lugar_nacimiento="Caracas",
        )


def test_paciente_lugar_nacimiento_vacio():
    """Verifica que un lugar de nacimiento vacío lance ValidationError."""
    with pytest.raises(ValidationError):
        PacienteCreate(
            nombre1="Juan",
            apellido1="Pérez",
            fecha_nacimiento="1990-01-01",
            lugar_nacimiento="",
        )

    with pytest.raises(ValidationError):
        PacienteCreate(
            nombre1="Juan",
            apellido1="Pérez",
            fecha_nacimiento="1990-01-01",
            lugar_nacimiento="   ",
        )


def test_paciente_fecha_normalizada():
    """Verifica que fecha_nacimiento en formato DD/MM/YYYY sea convertida y almacenada en formato ISO YYYY-MM-DD."""
    paciente = PacienteCreate(
        nombre1="Sofía",
        apellido1="Alvarado",
        fecha_nacimiento="15/05/1990",
        lugar_nacimiento="Turén",
    )
    assert paciente.fecha_nacimiento == "1990-05-15"

    paciente_guion = PacienteCreate(
        nombre1="Daniel",
        apellido1="Mendoza",
        fecha_nacimiento="31-12-1995",
        lugar_nacimiento="Guanare",
    )
    assert paciente_guion.fecha_nacimiento == "1995-12-31"


# ══════════════════════════════════════════════════════════════════
#  PRUEBAS DE TARJETACREATE
# ══════════════════════════════════════════════════════════════════

def test_tarjeta_create_valida():
    """Verifica la creación exitosa de TarjetaCreate con número de historia válido e id_paciente."""
    tarjeta = TarjetaCreate(
        num_historia="03-77-34",
        id_paciente=1,
    )
    assert tarjeta.num_historia == "03-77-34"
    assert tarjeta.id_paciente == 1
    assert tarjeta.id_color == 0
    assert tarjeta.estado == 1


def test_tarjeta_num_historia_invalido():
    """Verifica que un número de historia no numérico o con formato inválido lance ValidationError."""
    with pytest.raises(ValidationError):
        TarjetaCreate(
            num_historia="invalid",
            id_paciente=1,
        )

    with pytest.raises(ValidationError):
        TarjetaCreate(
            num_historia="03-77-3A",
            id_paciente=1,
        )


def test_tarjeta_num_historia_formato_parcial():
    """Verifica que un número de historia incompleto como '03-77' lance ValidationError."""
    with pytest.raises(ValidationError):
        TarjetaCreate(
            num_historia="03-77",
            id_paciente=1,
        )


# ══════════════════════════════════════════════════════════════════
#  PRUEBAS DE USUARIOCREATE
# ══════════════════════════════════════════════════════════════════

def test_usuario_create_valido():
    """Verifica la creación válida de un usuario con todos los campos obligatorios y opcionales."""
    usuario = UsuarioCreate(
        nombre="Juan",
        apellido="Pérez",
        cedula=12345678,
        usuario="jperez",
        clave="claveSegura123",
        pregunta1="¿Color favorito?",
        respuesta1="azul",
        pregunta2="¿Mascota?",
        respuesta2="perro",
        pregunta3="¿Ciudad natal?",
        respuesta3="caracas",
    )
    assert usuario.nombre == "Juan"
    assert usuario.apellido == "Pérez"
    assert usuario.cedula == 12345678
    assert usuario.usuario == "jperez"
    assert usuario.clave == "claveSegura123"
    assert usuario.estado == 1
    assert usuario.pregunta1 == "¿Color favorito?"
    assert usuario.respuesta1 == "azul"


def test_usuario_create_campos_obligatorios():
    """Verifica que falte cualquiera de los campos obligatorios lance ValidationError."""
    datos_base = {
        "nombre": "Juan",
        "apellido": "Pérez",
        "cedula": 12345678,
        "usuario": "jperez",
        "clave": "clave123",
    }

    # Cada uno de los campos obligatorios debe provocar ValidationError al faltar
    for campo in ["nombre", "apellido", "cedula", "usuario", "clave"]:
        datos_incompletos = {k: v for k, v in datos_base.items() if k != campo}
        with pytest.raises(ValidationError):
            UsuarioCreate(**datos_incompletos)
