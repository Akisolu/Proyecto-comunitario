from dao.usuario import UsuarioDAO
from models.usuario import Usuario


class AuthController:
    """Controlador de autenticación.
    Conecta la Vista de login con el UsuarioDAO para validar credenciales.
    """

    def __init__(self):
        self.usuario_dao = UsuarioDAO()
        self.usuario_actual: Usuario | None = None

    def login(self, nombre_usuario: str, clave: str) -> tuple[bool, str]:
        """Intenta autenticar al usuario.

        Args:
            nombre_usuario: Nombre de usuario ingresado.
            clave: Contraseña en texto plano ingresada.

        Returns:
            Tupla (éxito: bool, mensaje: str).
            Si éxito es True, self.usuario_actual queda seteado con el Usuario autenticado.
        """
        # Validaciones básicas de campos vacíos
        if not nombre_usuario or not nombre_usuario.strip():
            return False, "El campo de usuario no puede estar vacío."

        if not clave or not clave.strip():
            return False, "El campo de contraseña no puede estar vacío."

        nombre_usuario = nombre_usuario.strip()
        clave = clave.strip()

        try:
            usuario = self.usuario_dao.validar_credenciales(nombre_usuario, clave)

            if usuario is not None:
                self.usuario_actual = usuario
                return True, f"Bienvenido/a, {usuario.nombre} {usuario.apellido}."

            return False, "Usuario o contraseña incorrectos."

        except Exception as e:
            return False, f"Error al conectar con la base de datos: {str(e)}"

    def logout(self):
        """Cierra la sesión del usuario actual."""
        self.usuario_actual = None

    def obtener_usuario_actual(self) -> Usuario | None:
        """Retorna el usuario autenticado actualmente, o None si no hay sesión."""
        return self.usuario_actual

    def obtener_preguntas_seguridad(self, nombre_usuario: str) -> tuple[bool, str | list[str], int | None]:
        """Busca a un usuario por nombre de usuario y devuelve sus preguntas de seguridad."""
        if not nombre_usuario or not nombre_usuario.strip():
            return False, "Debe ingresar el nombre de usuario.", None

        usuario = self.usuario_dao.obtener_por_usuario(nombre_usuario.strip())
        if not usuario:
            return False, "Usuario no encontrado o inactivo.", None

        preguntas = [
            usuario.pregunta1,
            usuario.pregunta2,
            usuario.pregunta3
        ]
        
        if not all(preguntas):
            return False, "El usuario no tiene configuradas todas las preguntas de seguridad.", None

        return True, preguntas, usuario.id

    def verificar_respuesta_seguridad(self, id_usuario: int, indice_pregunta: int, respuesta: str) -> bool:
        """Verifica si la respuesta a una pregunta de seguridad es correcta."""
        if not respuesta or not respuesta.strip():
            return False

        usuario = self.usuario_dao.obtener_por_id(id_usuario)
        if not usuario:
            return False

        # El indice de pregunta (0, 1, 2) corresponde a respuesta1, respuesta2, respuesta3
        respuestas_correctas = [usuario.respuesta1, usuario.respuesta2, usuario.respuesta3]
        
        try:
            respuesta_correcta = respuestas_correctas[indice_pregunta]
        except IndexError:
            return False
            
        if not respuesta_correcta:
            return False

        # Comparamos en minúsculas para evitar problemas de case sensitivity
        return respuesta.strip().lower() == respuesta_correcta.lower()

    def recuperar_clave(self, id_usuario: int, nueva_clave: str, confirmacion: str) -> tuple[bool, str]:
        """Permite cambiar la contraseña si se han superado las preguntas de seguridad."""
        if not nueva_clave or not nueva_clave.strip():
            return False, "Debe ingresar la nueva contraseña."

        if len(nueva_clave.strip()) < 4:
            return False, "La nueva contraseña debe tener al menos 4 caracteres."

        if nueva_clave != confirmacion:
            return False, "La nueva contraseña y la confirmación no coinciden."

        exito = self.usuario_dao.resetear_clave(id_usuario, nueva_clave.strip())
        if exito:
            return True, "Contraseña actualizada exitosamente. Puede iniciar sesión."
        return False, "Error al actualizar la contraseña."
