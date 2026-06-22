import sqlite3
import hashlib
from models.usuario import UsuarioCreate, Usuario
from dao.conexion import ConexionDB


class UsuarioDAO:
    """DAO para operaciones CRUD y autenticación sobre la tabla 'usuarios'."""

    def __init__(self):
        self.db = ConexionDB()

    @staticmethod
    def _hash_clave(clave: str) -> str:
        """Genera un hash SHA-256 de la contraseña para almacenamiento seguro."""
        return hashlib.sha256(clave.encode("utf-8")).hexdigest()

    def crear(self, usuario: UsuarioCreate) -> int:
        """Registra un nuevo usuario con la contraseña hasheada.
        Retorna el id del usuario creado, o -1 si el usuario/cédula ya existe.
        """
        conn = self.db.obtener_conexion()
        cursor = conn.cursor()
        query = """
            INSERT INTO usuarios
                (nombre, apellido, cedula, usuario, clave, estado,
                 pregunta1, respuesta1, pregunta2, respuesta2, pregunta3, respuesta3)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?)
        """
        try:
            clave_hash = self._hash_clave(usuario.clave)
            cursor.execute(query, (
                usuario.nombre,
                usuario.apellido,
                usuario.cedula,
                usuario.usuario,
                clave_hash,
                usuario.pregunta1,
                usuario.respuesta1.lower() if usuario.respuesta1 else None,
                usuario.pregunta2,
                usuario.respuesta2.lower() if usuario.respuesta2 else None,
                usuario.pregunta3,
                usuario.respuesta3.lower() if usuario.respuesta3 else None,
            ))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return -1
        finally:
            conn.close()

    def obtener_por_id(self, id_usuario: int) -> Usuario | None:
        """Obtiene un usuario activo por su ID."""
        conn = self.db.obtener_conexion()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nombre, apellido, cedula, usuario, estado, "
            "pregunta1, respuesta1, pregunta2, respuesta2, pregunta3, respuesta3 "
            "FROM usuarios WHERE id = ? AND estado = 1",
            (id_usuario,)
        )
        fila = cursor.fetchone()
        conn.close()
        return Usuario(**dict(fila)) if fila else None

    def obtener_todos(self) -> list[Usuario]:
        """Obtiene todos los usuarios activos."""
        conn = self.db.obtener_conexion()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nombre, apellido, cedula, usuario, estado, "
            "pregunta1, respuesta1, pregunta2, respuesta2, pregunta3, respuesta3 "
            "FROM usuarios WHERE estado = 1"
        )
        filas = cursor.fetchall()
        conn.close()
        return [Usuario(**dict(fila)) for fila in filas]

    def actualizar(self, id_usuario: int, usuario: UsuarioCreate) -> bool:
        """Actualiza los datos de un usuario activo (incluyendo contraseña).
        Retorna True si se actualizó al menos un registro.
        """
        conn = self.db.obtener_conexion()
        cursor = conn.cursor()
        query = """
            UPDATE usuarios
            SET nombre = ?, apellido = ?, cedula = ?,
                usuario = ?, clave = ?,
                pregunta1 = ?, respuesta1 = ?,
                pregunta2 = ?, respuesta2 = ?,
                pregunta3 = ?, respuesta3 = ?
            WHERE id = ? AND estado = 1
        """
        try:
            clave_hash = self._hash_clave(usuario.clave)
            cursor.execute(query, (
                usuario.nombre,
                usuario.apellido,
                usuario.cedula,
                usuario.usuario,
                clave_hash,
                usuario.pregunta1,
                usuario.respuesta1.lower() if usuario.respuesta1 else None,
                usuario.pregunta2,
                usuario.respuesta2.lower() if usuario.respuesta2 else None,
                usuario.pregunta3,
                usuario.respuesta3.lower() if usuario.respuesta3 else None,
                id_usuario,
            ))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def soft_delete(self, id_usuario: int) -> bool:
        """Desactiva (borrado lógico) un usuario.
        Retorna True si se desactivó al menos un registro.
        """
        conn = self.db.obtener_conexion()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE usuarios SET estado = 0 WHERE id = ? AND estado = 1",
                (id_usuario,)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def validar_credenciales(self, nombre_usuario: str, clave: str) -> Usuario | None:
        """Valida las credenciales de login.
        Compara el hash de la contraseña proporcionada contra el almacenado.
        Retorna el objeto Usuario si las credenciales son válidas, None en caso contrario.
        """
        conn = self.db.obtener_conexion()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nombre, apellido, cedula, usuario, clave, estado, "
            "pregunta1, respuesta1, pregunta2, respuesta2, pregunta3, respuesta3 "
            "FROM usuarios WHERE usuario = ? AND estado = 1",
            (nombre_usuario,)
        )
        fila = cursor.fetchone()
        conn.close()

        if fila is None:
            return None

        fila_dict = dict(fila)
        clave_hash_almacenada = fila_dict.pop("clave")
        clave_hash_ingresada = self._hash_clave(clave)

        if clave_hash_almacenada == clave_hash_ingresada:
            return Usuario(**fila_dict)

        return None

    def cambiar_clave(
        self, id_usuario: int, clave_actual: str, clave_nueva: str
    ) -> tuple[bool, str]:
        """Cambia la contraseña de un usuario verificando la clave actual.

        Primero verifica que el hash de la clave actual coincida con el
        almacenado. Solo si coincide, actualiza con el hash de la nueva clave.

        Args:
            id_usuario:   ID del usuario.
            clave_actual: Contraseña actual en texto plano.
            clave_nueva:  Nueva contraseña en texto plano.

        Returns:
            Tupla (exito, mensaje).
        """
        conn = self.db.obtener_conexion()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Obtener hash actual almacenado
        cursor.execute(
            "SELECT clave FROM usuarios WHERE id = ? AND estado = 1",
            (id_usuario,),
        )
        fila = cursor.fetchone()
        if fila is None:
            conn.close()
            return False, "Usuario no encontrado o inactivo."

        hash_actual_almacenado = fila["clave"]
        hash_actual_ingresado = self._hash_clave(clave_actual)

        if hash_actual_almacenado != hash_actual_ingresado:
            conn.close()
            return False, "La contraseña actual es incorrecta."

        # Actualizar con la nueva clave hasheada
        hash_nueva = self._hash_clave(clave_nueva)
        cursor.execute(
            "UPDATE usuarios SET clave = ? WHERE id = ? AND estado = 1",
            (hash_nueva, id_usuario),
        )
        conn.commit()
        conn.close()
        return True, "Contraseña actualizada exitosamente."

    def obtener_por_usuario(self, nombre_usuario: str) -> Usuario | None:
        """Obtiene un usuario activo por su nombre de usuario (para recuperación)."""
        conn = self.db.obtener_conexion()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nombre, apellido, cedula, usuario, estado, "
            "pregunta1, respuesta1, pregunta2, respuesta2, pregunta3, respuesta3 "
            "FROM usuarios WHERE usuario = ? AND estado = 1",
            (nombre_usuario,)
        )
        fila = cursor.fetchone()
        conn.close()
        return Usuario(**dict(fila)) if fila else None

    def resetear_clave(self, id_usuario: int, nueva_clave: str) -> bool:
        """Fuerza el cambio de contraseña (para recuperación)."""
        conn = self.db.obtener_conexion()
        cursor = conn.cursor()
        hash_nueva = self._hash_clave(nueva_clave)
        cursor.execute(
            "UPDATE usuarios SET clave = ? WHERE id = ? AND estado = 1",
            (hash_nueva, id_usuario),
        )
        exito = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return exito

