"""
Pruebas unitarias para ConexionDB, LoggingConnection y LoggingCursor (Capa de Conexión y Diagnóstico).

Verifica la inicialización de rutas de base de datos, creación de directorios,
simulación de fallos de disco o permisos, wrappers de logging para cursores y
conexiones, detección de cuellos de botella (>100 ms) y propagación controlada de errores SQL.
"""

import os
import sqlite3
import pytest
from dao.conexion import ConexionDB, LoggingConnection, LoggingCursor


def test_conexion_db_rutas_por_defecto_y_personalizada(tmp_path):
    """Verifica que ConexionDB calcule la ruta por defecto o acepte una ruta explícita."""
    # Por defecto
    db_default = ConexionDB()
    assert db_default.db_path.endswith(os.path.join("database", "database.db"))

    # Ruta personalizada
    custom_path = str(tmp_path / "subdir" / "test.db")
    db_custom = ConexionDB(custom_path)
    assert db_custom.db_path == custom_path


def test_obtener_conexion_crea_directorio_y_conecta(tmp_path):
    """Verifica que obtener_conexion cree el directorio padre si no existe y retorne LoggingConnection."""
    target_dir = tmp_path / "nueva_carpeta_db"
    db_file = str(target_dir / "hospital.db")
    assert not target_dir.exists()

    db_obj = ConexionDB(db_file)
    conn = db_obj.obtener_conexion()

    assert target_dir.exists()
    assert isinstance(conn, LoggingConnection)
    conn.close()


def test_obtener_conexion_fallo_creacion_directorio(monkeypatch, tmp_path):
    """Simula un fallo de disco o permisos protegidos al intentar crear el directorio de la BD."""
    db_file = str(tmp_path / "sin_permiso" / "test.db")
    db_obj = ConexionDB(db_file)

    def _fake_makedirs(*args, **kwargs):
        raise PermissionError("Acceso denegado al sistema de archivos")

    monkeypatch.setattr(os, "makedirs", _fake_makedirs)

    with pytest.raises(PermissionError, match="Acceso denegado"):
        db_obj.obtener_conexion()


def test_obtener_conexion_fallo_sqlite_connect(monkeypatch, tmp_path):
    """Simula un fallo del motor SQLite al intentar conectarse al archivo."""
    db_file = str(tmp_path / "corrupt.db")
    db_obj = ConexionDB(db_file)

    def _fake_connect(*args, **kwargs):
        raise sqlite3.OperationalError("unable to open database file")

    monkeypatch.setattr(sqlite3, "connect", _fake_connect)

    with pytest.raises(sqlite3.OperationalError, match="unable to open database file"):
        db_obj.obtener_conexion()


def test_logging_connection_wrapper():
    """Verifica que LoggingConnection delegue atributos y context managers correctamente."""
    raw_conn = sqlite3.connect(":memory:")
    log_conn = LoggingConnection(raw_conn)

    # __getattr__ y cursor()
    cursor = log_conn.cursor()
    assert isinstance(cursor, LoggingCursor)

    # __setattr__ personalizado
    log_conn.custom_prop = "valor_prueba"
    assert log_conn.custom_prop == "valor_prueba"

    # Context manager __enter__ y __exit__
    with log_conn as c:
        assert c is log_conn

    raw_conn.close()


def test_logging_cursor_execute_y_cuello_de_botella(monkeypatch):
    """Verifica que LoggingCursor registre consultas normales y advierta sobre cuellos de botella."""
    raw_conn = sqlite3.connect(":memory:")
    cursor = LoggingCursor(raw_conn.cursor())

    # 1. Consulta rápida normal
    cursor.execute("CREATE TABLE test (id INT, nombre TEXT)")
    cursor.execute("INSERT INTO test VALUES (?, ?)", (1, "Prueba"))
    cursor.execute("SELECT * FROM test")
    fila = cursor.fetchone()
    assert fila == (1, "Prueba")

    # 2. Simular consulta lenta (> 100 ms) para cubrir la rama de cuello de botella
    tiempos = [0.0, 0.150]  # 150 ms de diferencia
    monkeypatch.setattr("time.perf_counter", lambda: tiempos.pop(0) if tiempos else 0.200)

    cursor.execute("SELECT * FROM test")

    # 3. Iteración y next
    cursor.execute("SELECT 1 UNION SELECT 2")
    filas = list(cursor)
    assert len(filas) == 2

    raw_conn.close()


def test_logging_cursor_execute_error():
    """Verifica que un error SQL en execute sea registrado y relanzado."""
    raw_conn = sqlite3.connect(":memory:")
    cursor = LoggingCursor(raw_conn.cursor())

    with pytest.raises(sqlite3.OperationalError):
        cursor.execute("SELECT * FROM tabla_que_no_existe")

    raw_conn.close()


def test_logging_cursor_executemany_y_error():
    """Verifica el funcionamiento y captura de errores de executemany."""
    raw_conn = sqlite3.connect(":memory:")
    cursor = LoggingCursor(raw_conn.cursor())
    cursor.execute("CREATE TABLE items (id INT, valor TEXT)")

    # Exitoso
    cursor.executemany("INSERT INTO items VALUES (?, ?)", [(1, "A"), (2, "B")])
    cursor.execute("SELECT COUNT(*) FROM items")
    assert cursor.fetchone()[0] == 2

    # Error
    with pytest.raises(sqlite3.OperationalError):
        cursor.executemany("INSERT INTO tabla_inexistente VALUES (?)", [(1,)])

    raw_conn.close()


def test_logging_cursor_executescript_y_error():
    """Verifica el funcionamiento y captura de errores de executescript."""
    raw_conn = sqlite3.connect(":memory:")
    cursor = LoggingCursor(raw_conn.cursor())

    script_valido = """
        CREATE TABLE config (clave TEXT, valor TEXT);
        INSERT INTO config VALUES ('tema', 'oscuro');
    """
    cursor.executescript(script_valido)
    cursor.execute("SELECT valor FROM config WHERE clave = 'tema'")
    assert cursor.fetchone()[0] == "oscuro"

    # Script con error de sintaxis
    script_invalido = "ESTO NO ES SQL VALIDO;"
    with pytest.raises(sqlite3.OperationalError):
        cursor.executescript(script_invalido)

    raw_conn.close()
