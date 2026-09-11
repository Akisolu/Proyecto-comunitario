import os
import sqlite3 as db
import time
from loguru import logger

class LoggingCursor:
    """Wrapper para el cursor de sqlite3 que registra el rendimiento y errores de las consultas SQL."""
    def __init__(self, cursor):
        self.__dict__['_cursor'] = cursor

    def __getattr__(self, name):
        return getattr(self._cursor, name)

    def __setattr__(self, name, value):
        if name == '_cursor':
            self.__dict__['_cursor'] = value
        else:
            setattr(self._cursor, name, value)

    def __iter__(self):
        return iter(self._cursor)

    def __next__(self):
        return next(self._cursor)

    def _log_query(self, method_name, sql, parameters, execution_time_ms):
        # Umbral de cuello de botella: 100 ms
        UMBRAL_MS = 100.0
        if execution_time_ms >= UMBRAL_MS:
            logger.warning(
                f"[CUELLO DE BOTELLA] Consulta lenta detectada ({method_name}) | "
                f"SQL: {sql.strip()} | Params: {parameters} | Tiempo: {execution_time_ms:.2f} ms"
            )
        else:
            logger.success(
                f"SQL {method_name}: {sql.strip()} | Params: {parameters} | Tiempo: {execution_time_ms:.2f} ms"
            )

    def execute(self, sql, parameters=()):
        inicio = time.perf_counter()
        try:
            res = self._cursor.execute(sql, parameters)
            fin = time.perf_counter()
            self._log_query("Execute", sql, parameters, (fin - inicio) * 1000)
            return res
        except Exception as e:
            logger.error(f"SQL Error en Execute: {sql.strip()} | Params: {parameters} | Error: {e}")
            raise

    def executemany(self, sql, seq_of_parameters):
        inicio = time.perf_counter()
        try:
            res = self._cursor.executemany(sql, seq_of_parameters)
            fin = time.perf_counter()
            self._log_query("ExecuteMany", sql, f"({len(seq_of_parameters)} registros)", (fin - inicio) * 1000)
            return res
        except Exception as e:
            logger.error(f"SQL Error en ExecuteMany: {sql.strip()} | Count: {len(seq_of_parameters)} | Error: {e}")
            raise

    def executescript(self, sql_script):
        inicio = time.perf_counter()
        try:
            res = self._cursor.executescript(sql_script)
            fin = time.perf_counter()
            self._log_query("ExecuteScript", "[Script SQL]", (), (fin - inicio) * 1000)
            return res
        except Exception as e:
            logger.error(f"SQL Error en ExecuteScript | Error: {e}")
            raise


class LoggingConnection:
    """Wrapper para la conexión de sqlite3 que devuelve un LoggingCursor y delega el resto."""
    def __init__(self, conn):
        self.__dict__['_conn'] = conn

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def __setattr__(self, name, value):
        if name == '_conn':
            self.__dict__['_conn'] = value
            return

        try:
            setattr(self._conn, name, value)
        except AttributeError:
            self.__dict__[name] = value

    def __enter__(self):
        self._conn.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._conn.__exit__(exc_type, exc_val, exc_tb)

    def cursor(self, *args, **kwargs):
        real_cursor = self._conn.cursor(*args, **kwargs)
        return LoggingCursor(real_cursor)


class ConexionDB:
    def __init__(self, db_path=None):
        if db_path is None:
            # Calcular ruta absoluta basada en la ubicación de este archivo (src/dao/conexion.py)
            # Volver 3 niveles arriba: dao -> src -> raíz
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.db_path = os.path.join(base_dir, "database", "database.db")
        else:
            self.db_path = db_path

    def obtener_conexion(self):
        # Asegurar de que la base de datos se cree en la carpeta adecuada
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = db.connect(self.db_path, check_same_thread=False)
        return LoggingConnection(conn)