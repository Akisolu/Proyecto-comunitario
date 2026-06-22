from pydantic import ValidationError
from dao.usuario import UsuarioDAO
from models.usuario import UsuarioCreate, Usuario


class UsuarioController:
    """Controlador de usuarios.
    Orquesta el CRUD de usuarios con validacion Pydantic.
    """

    def __init__(self):
        self.usuario_dao = UsuarioDAO()

    def registrar_usuario(self, datos: dict) -> tuple[bool, str]:
        """Registra un nuevo usuario.

        Args:
            datos: Diccionario con nombre, apellido, cedula, usuario, clave.

        Returns:
            Tupla (exito, mensaje).
        """
        errores = self._validar_preguntas_seguridad(datos)
        if errores:
            return False, "Errores de validacion:\n" + "\n".join(errores)

        try:
            usuario = UsuarioCreate(**datos)
        except ValidationError as e:
            errores = []
            for error in e.errors():
                campo = " -> ".join(str(loc) for loc in error["loc"])
                errores.append(f"  {campo}: {error['msg']}")
            return False, "Errores de validacion:\n" + "\n".join(errores)

        id_usuario = self.usuario_dao.crear(usuario)

        if id_usuario == -1:
            return False, "Ya existe un usuario con esa cedula o nombre de usuario."

        return True, f"Usuario registrado exitosamente (ID: {id_usuario})."

    def listar_usuarios(self) -> list[Usuario]:
        """Retorna todos los usuarios activos."""
        return self.usuario_dao.obtener_todos()

    def obtener_usuario(self, id_usuario: int) -> tuple[bool, str | Usuario]:
        """Obtiene un usuario por ID."""
        usuario = self.usuario_dao.obtener_por_id(id_usuario)
        if usuario is None:
            return False, "Usuario no encontrado o inactivo."
        return True, usuario

    def actualizar_usuario(
        self, id_usuario: int, datos: dict
    ) -> tuple[bool, str]:
        """Actualiza un usuario existente.

        Args:
            id_usuario: ID del usuario a actualizar.
            datos: Diccionario con los campos actualizados (incluyendo clave).

        Returns:
            Tupla (exito, mensaje).
        """
        errores = self._validar_preguntas_seguridad(datos)
        if errores:
            return False, "Errores de validacion:\n" + "\n".join(errores)

        try:
            usuario = UsuarioCreate(**datos)
        except ValidationError as e:
            errores = []
            for error in e.errors():
                campo = " -> ".join(str(loc) for loc in error["loc"])
                errores.append(f"  {campo}: {error['msg']}")
            return False, "Errores de validacion:\n" + "\n".join(errores)

        actualizado = self.usuario_dao.actualizar(id_usuario, usuario)

        if not actualizado:
            return False, "No se pudo actualizar. Cedula o usuario duplicado."

        return True, "Usuario actualizado exitosamente."

    def eliminar_usuario(self, id_usuario: int) -> tuple[bool, str]:
        """Desactiva un usuario (borrado logico)."""
        eliminado = self.usuario_dao.soft_delete(id_usuario)
        if not eliminado:
            return False, "No se pudo desactivar el usuario."
        return True, "Usuario desactivado exitosamente."

    def cambiar_clave(
        self,
        id_usuario: int,
        clave_actual: str,
        clave_nueva: str,
        clave_confirmacion: str,
    ) -> tuple[bool, str]:
        """Cambia la contraseña de un usuario con verificación.

        Valida que:
        - Los campos no estén vacíos.
        - La nueva clave tenga mínimo 4 caracteres.
        - La nueva clave y la confirmación coincidan.
        - La clave actual sea correcta (verificada contra el hash en BD).

        Args:
            id_usuario:         ID del usuario.
            clave_actual:       Contraseña actual en texto plano.
            clave_nueva:        Nueva contraseña en texto plano.
            clave_confirmacion: Confirmación de la nueva contraseña.

        Returns:
            Tupla (exito, mensaje).
        """
        if not clave_actual or not clave_actual.strip():
            return False, "Debe ingresar la contraseña actual."

        if not clave_nueva or not clave_nueva.strip():
            return False, "Debe ingresar la nueva contraseña."

        if len(clave_nueva.strip()) < 4:
            return False, "La nueva contraseña debe tener al menos 4 caracteres."

        if clave_nueva != clave_confirmacion:
            return False, "La nueva contraseña y la confirmación no coinciden."

        return self.usuario_dao.cambiar_clave(
            id_usuario, clave_actual.strip(), clave_nueva.strip()
        )

    def _validar_preguntas_seguridad(self, datos: dict) -> list[str]:
        """Valida que las preguntas y respuestas de seguridad estén presentes y no vacías."""
        errores = []
        for i in range(1, 4):
            preg = datos.get(f"pregunta{i}")
            resp = datos.get(f"respuesta{i}")
            if not preg or not str(preg).strip():
                errores.append(f"Pregunta de seguridad {i} es obligatoria.")
            if not resp or not str(resp).strip():
                errores.append(f"Respuesta de seguridad {i} es obligatoria.")
        return errores

