"""
Fixtures globales para la suite de pruebas de SGI Salud.

Proporciona:
    - Configuración de sys.path para importar módulos de src/
    - Base de datos SQLite en memoria con esquema cargado
    - Datos semilla (colores, servicios, usuario de prueba)
    - Patches automáticos para ConexionDB
"""

import sys
import os
import sqlite3

import pytest

# ── Asegurar que src/ esté en sys.path ────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

SCHEMA_PATH = os.path.join(PROJECT_ROOT, "database", "schema.sql")


# ── Colores semilla (deben coincidir con MAPA_COLORES) ────────────
COLORES_SEMILLA = [
    ("Marron",),
    ("Azul Marino",),
    ("Verde",),
    ("Naranja",),
    ("Morado",),
    ("Rosa",),
    ("Turquesa",),
    ("Amarillo",),
    ("Rojo",),
    ("Azul Celeste",),
]

# ── Servicios semilla ─────────────────────────────────────────────
SERVICIOS_SEMILLA = [
    ("Medicina Interna", 10),
    ("Pediatria", 8),
    ("Cirugia", 6),
    ("Obstetricia", 12),
]


def _crear_conexion_memoria() -> sqlite3.Connection:
    """Crea una conexión SQLite en memoria con el esquema del proyecto."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")

    if os.path.exists(SCHEMA_PATH):
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            sql = f.read()
        # El schema.sql usa BEGIN TRANSACTION / COMMIT, ejecutar como script
        conn.executescript(sql)
    else:
        raise FileNotFoundError(f"Esquema no encontrado en {SCHEMA_PATH}")

    return conn


def _sembrar_colores(conn: sqlite3.Connection):
    """Inserta los 10 colores base del sistema cromático."""
    cursor = conn.cursor()
    cursor.executemany(
        "INSERT OR IGNORE INTO colores (valor, estado) VALUES (?, 1)",
        COLORES_SEMILLA,
    )
    conn.commit()


def _sembrar_servicios(conn: sqlite3.Connection):
    """Inserta servicios hospitalarios de prueba."""
    cursor = conn.cursor()
    cursor.executemany(
        "INSERT OR IGNORE INTO servicios (nombre, total_camas, estado) VALUES (?, ?, 1)",
        SERVICIOS_SEMILLA,
    )
    conn.commit()


# ══════════════════════════════════════════════════════════════════
#  FIXTURES
# ══════════════════════════════════════════════════════════════════

@pytest.fixture
def db_conn():
    """Conexión SQLite en memoria con esquema cargado y datos semilla.

    Cada test recibe una conexión limpia e independiente.
    La conexión se cierra automáticamente al finalizar el test.
    """
    conn = _crear_conexion_memoria()
    _sembrar_colores(conn)
    _sembrar_servicios(conn)
    yield conn
    conn.close()


@pytest.fixture
def patch_conexion(db_conn, monkeypatch):
    """Parchea ConexionDB.obtener_conexion para que retorne la BD en memoria.

    IMPORTANTE: Cada llamada retorna una NUEVA LoggingConnection sobre
    la MISMA conexión subyacente, imitando el comportamiento real pero
    manteniendo el estado compartido durante el test.

    Además intercepta close() para que no cierre la conexión compartida
    durante la ejecución del test.
    """
    from dao.conexion import ConexionDB, LoggingConnection

    class _TestLoggingConnection(LoggingConnection):
        """Wrapper que intercepta close() para no cerrar la conexión compartida."""
        def close(self):
            pass  # No cerrar durante el test

        def __exit__(self, exc_type, exc_val, exc_tb):
            # Delegar manejo de transacción sin cerrar
            if exc_type is not None:
                self._conn.rollback()
            return False

    def _fake_obtener_conexion(self_db=None):
        return _TestLoggingConnection(db_conn)

    monkeypatch.setattr(ConexionDB, "obtener_conexion", _fake_obtener_conexion)
    return db_conn


@pytest.fixture
def usuario_semilla(patch_conexion):
    """Crea un usuario de prueba en la BD y retorna sus datos.

    Returns:
        dict con id, nombre, apellido, cedula, usuario, clave (texto plano).
    """
    from dao.usuario import UsuarioDAO
    from models.usuario import UsuarioCreate

    dao = UsuarioDAO()
    datos = UsuarioCreate(
        nombre="Juan",
        apellido="Pérez",
        cedula=12345678,
        usuario="jperez",
        clave="clave123",
        pregunta1="¿Color favorito?",
        respuesta1="azul",
        pregunta2="¿Mascota?",
        respuesta2="perro",
        pregunta3="¿Ciudad natal?",
        respuesta3="caracas",
    )
    id_usuario = dao.crear(datos)
    return {
        "id": id_usuario,
        "nombre": "Juan",
        "apellido": "Pérez",
        "cedula": 12345678,
        "usuario": "jperez",
        "clave": "clave123",
    }


@pytest.fixture
def paciente_semilla(patch_conexion):
    """Crea un paciente de prueba en la BD y retorna sus datos.

    Returns:
        dict con id y los datos del paciente.
    """
    from dao.paciente import PacienteDAO
    from models.paciente import PacienteCreate

    dao = PacienteDAO()
    datos = PacienteCreate(
        cedula="V-12345678",
        nombre1="María",
        nombre2="Elena",
        apellido1="González",
        apellido2="López",
        fecha_nacimiento="15/05/1990",
        lugar_nacimiento="Turén",
        estado_vital=1,
    )
    id_paciente = dao.crear(datos)
    return {
        "id": id_paciente,
        "cedula": "V-12345678",
        "nombre1": "María",
        "nombre2": "Elena",
        "apellido1": "González",
        "apellido2": "López",
        "fecha_nacimiento": "1990-05-15",
        "lugar_nacimiento": "Turén",
    }


@pytest.fixture
def paciente_con_tarjeta(paciente_semilla, patch_conexion):
    """Crea un paciente con tarjeta asignada.

    Returns:
        dict con datos del paciente e id_tarjeta y num_historia.
    """
    from dao.tarjeta import TarjetaDAO
    from dao.color import ColorDAO
    from models.tarjeta import TarjetaCreate

    tarjeta_dao = TarjetaDAO()
    color_dao = ColorDAO()

    # El número 03-77-34 → decena 3 → Naranja
    num_historia = "03-77-34"
    color = color_dao.obtener_por_valor("Naranja")
    tarjeta = TarjetaCreate(
        num_historia=num_historia,
        id_paciente=paciente_semilla["id"],
        id_color=color.id,
    )
    id_tarjeta = tarjeta_dao.crear(tarjeta)

    return {
        **paciente_semilla,
        "id_tarjeta": id_tarjeta,
        "num_historia": num_historia,
    }
