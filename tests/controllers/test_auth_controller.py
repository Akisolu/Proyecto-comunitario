"""Pruebas unitarias para el controlador de autenticación (AuthController).

Módulo bajo prueba: controllers.auth_controller
Valida:
    - Inicio de sesión con credenciales válidas e inválidas
    - Validación de campos vacíos en el login
    - Cierre de sesión y estado del usuario actual
    - Consulta de preguntas de seguridad de un usuario
    - Verificación de respuestas de seguridad (sensibilidad a mayúsculas/minúsculas)
    - Recuperación y reseteo de contraseñas con validaciones de longitud y confirmación
"""

import pytest
from controllers.auth_controller import AuthController


def test_login_exitoso(usuario_semilla):
    """Verifica el inicio de sesión exitoso con credenciales válidas."""
    controller = AuthController()
    exito, mensaje = controller.login("jperez", "clave123")

    assert exito is True
    assert "Bienvenido" in mensaje
    usuario_actual = controller.obtener_usuario_actual()
    assert usuario_actual is not None
    assert usuario_actual.usuario == "jperez"
    assert usuario_actual.id == usuario_semilla["id"]


def test_login_clave_incorrecta(usuario_semilla):
    """Verifica que el inicio de sesión falle cuando la contraseña es errónea."""
    controller = AuthController()
    exito, mensaje = controller.login("jperez", "wrong")

    assert exito is False
    assert "incorrectos" in mensaje.lower()
    assert controller.obtener_usuario_actual() is None


def test_login_usuario_inexistente(patch_conexion):
    """Verifica que el inicio de sesión falle con un usuario que no existe."""
    controller = AuthController()
    exito, mensaje = controller.login("noexiste", "x")

    assert exito is False
    assert "incorrectos" in mensaje.lower()
    assert controller.obtener_usuario_actual() is None


def test_login_campo_vacio(patch_conexion):
    """Verifica la validación de campos obligatorios vacíos o con solo espacios."""
    controller = AuthController()

    # Usuario vacío
    exito, mensaje = controller.login("", "clave123")
    assert exito is False
    assert "usuario no puede estar vacío" in mensaje.lower()

    exito, mensaje = controller.login("   ", "clave123")
    assert exito is False
    assert "usuario no puede estar vacío" in mensaje.lower()

    # Contraseña vacía
    exito, mensaje = controller.login("jperez", "")
    assert exito is False
    assert "contraseña no puede estar vacío" in mensaje.lower()

    exito, mensaje = controller.login("jperez", "   ")
    assert exito is False
    assert "contraseña no puede estar vacío" in mensaje.lower()

    assert controller.obtener_usuario_actual() is None


def test_logout(usuario_semilla):
    """Verifica que cerrar sesión limpie el usuario autenticado actualmente."""
    controller = AuthController()
    exito, _ = controller.login("jperez", "clave123")
    assert exito is True
    assert controller.obtener_usuario_actual() is not None

    controller.logout()
    assert controller.obtener_usuario_actual() is None


def test_obtener_preguntas_seguridad(usuario_semilla):
    """Verifica la obtención correcta de las 3 preguntas de seguridad configuradas."""
    controller = AuthController()
    exito, preguntas, id_usuario = controller.obtener_preguntas_seguridad("jperez")

    assert exito is True
    assert isinstance(preguntas, list)
    assert len(preguntas) == 3
    assert preguntas[0] == "¿Color favorito?"
    assert preguntas[1] == "¿Mascota?"
    assert preguntas[2] == "¿Ciudad natal?"
    assert id_usuario == usuario_semilla["id"]


def test_obtener_preguntas_seguridad_usuario_inexistente(patch_conexion):
    """Verifica el error al solicitar preguntas de un usuario que no existe."""
    controller = AuthController()
    exito, mensaje, id_usuario = controller.obtener_preguntas_seguridad("desconocido")

    assert exito is False
    assert "no encontrado" in mensaje.lower()
    assert id_usuario is None


def test_obtener_preguntas_seguridad_campo_vacio(patch_conexion):
    """Verifica el error al solicitar preguntas con nombre de usuario en blanco."""
    controller = AuthController()
    exito, mensaje, id_usuario = controller.obtener_preguntas_seguridad("   ")

    assert exito is False
    assert "debe ingresar" in mensaje.lower()
    assert id_usuario is None


def test_verificar_respuesta_correcta(usuario_semilla):
    """Verifica que la respuesta de seguridad correcta retorne True."""
    controller = AuthController()
    id_usuario = usuario_semilla["id"]

    assert controller.verificar_respuesta_seguridad(id_usuario, 0, "azul") is True
    assert controller.verificar_respuesta_seguridad(id_usuario, 1, "perro") is True
    assert controller.verificar_respuesta_seguridad(id_usuario, 2, "caracas") is True


def test_verificar_respuesta_incorrecta(usuario_semilla):
    """Verifica que una respuesta errónea o índice inválido retorne False."""
    controller = AuthController()
    id_usuario = usuario_semilla["id"]

    # Respuesta errónea
    assert controller.verificar_respuesta_seguridad(id_usuario, 0, "rojo") is False

    # Índice de pregunta fuera de rango
    assert controller.verificar_respuesta_seguridad(id_usuario, 99, "azul") is False

    # Respuesta vacía
    assert controller.verificar_respuesta_seguridad(id_usuario, 0, "") is False
    assert controller.verificar_respuesta_seguridad(id_usuario, 0, "   ") is False

    # Usuario inexistente
    assert controller.verificar_respuesta_seguridad(99999, 0, "azul") is False


def test_verificar_respuesta_case_insensitive(usuario_semilla):
    """Verifica que la comparación de respuestas no distinga entre mayúsculas y minúsculas."""
    controller = AuthController()
    id_usuario = usuario_semilla["id"]

    assert controller.verificar_respuesta_seguridad(id_usuario, 0, "AZUL") is True
    assert controller.verificar_respuesta_seguridad(id_usuario, 0, "AzUl") is True
    assert controller.verificar_respuesta_seguridad(id_usuario, 0, "  AZUL  ") is True


def test_recuperar_clave_exitoso(usuario_semilla):
    """Verifica el reseteo exitoso de la clave y posterior autenticación con la nueva."""
    controller = AuthController()
    id_usuario = usuario_semilla["id"]

    exito, mensaje = controller.recuperar_clave(id_usuario, "nueva1234", "nueva1234")
    assert exito is True
    assert "exitosamente" in mensaje.lower()

    # Iniciar sesión con la nueva contraseña debe funcionar
    exito_login, msg_login = controller.login("jperez", "nueva1234")
    assert exito_login is True
    assert "Bienvenido" in msg_login

    # La contraseña vieja ya no debe funcionar
    controller.logout()
    exito_vieja, _ = controller.login("jperez", "clave123")
    assert exito_vieja is False


def test_recuperar_clave_no_coincide(usuario_semilla):
    """Verifica el error cuando la confirmación no coincide con la nueva clave."""
    controller = AuthController()
    id_usuario = usuario_semilla["id"]

    exito, mensaje = controller.recuperar_clave(id_usuario, "nueva1234", "otra5678")
    assert exito is False
    assert "no coinciden" in mensaje.lower()


def test_recuperar_clave_muy_corta(usuario_semilla):
    """Verifica el error cuando la nueva contraseña tiene menos de 4 caracteres."""
    controller = AuthController()
    id_usuario = usuario_semilla["id"]

    exito, mensaje = controller.recuperar_clave(id_usuario, "abc", "abc")
    assert exito is False
    assert "al menos 4 caracteres" in mensaje.lower()


def test_recuperar_clave_vacia(usuario_semilla):
    """Verifica el error cuando la nueva contraseña está vacía."""
    controller = AuthController()
    id_usuario = usuario_semilla["id"]

    exito, mensaje = controller.recuperar_clave(id_usuario, "", "")
    assert exito is False
    assert "debe ingresar la nueva contraseña" in mensaje.lower()
