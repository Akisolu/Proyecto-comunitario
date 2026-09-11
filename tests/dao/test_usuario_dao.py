"""
Pruebas unitarias para UsuarioDAO (Capa de Acceso a Datos y Autenticación de Usuarios).

Verifica la creación con hash criptográfico SHA-256, unicidad de cédula y username,
validación de credenciales de acceso, cambio y reseteo de contraseñas, consultas
y borrado lógico de operadores.
"""

import pytest
from dao.usuario import UsuarioDAO
from models.usuario import UsuarioCreate, Usuario


def test_hash_no_es_texto_plano(patch_conexion):
    """Verifica que la contraseña se guarde como hash SHA-256 y nunca en texto plano."""
    dao = UsuarioDAO()
    datos = UsuarioCreate(
        nombre="Test",
        apellido="User",
        cedula=99999999,
        usuario="testuser",
        clave="miPassword",
    )
    dao.crear(datos)

    cursor = patch_conexion.cursor()
    cursor.execute("SELECT clave FROM usuarios WHERE usuario='testuser'")
    row = cursor.fetchone()

    assert row is not None
    assert row[0] != "miPassword"
    assert len(row[0]) == 64  # Longitud del digest hexadecimal SHA-256


def test_crear_usuario_exitoso(patch_conexion):
    """Verifica la creación exitosa de un usuario retornando un ID positivo."""
    dao = UsuarioDAO()
    datos = UsuarioCreate(
        nombre="Ana",
        apellido="López",
        cedula=23456789,
        usuario="alopez",
        clave="segura123",
    )
    id_usuario = dao.crear(datos)
    assert id_usuario > 0

    usuario = dao.obtener_por_id(id_usuario)
    assert usuario is not None
    assert usuario.usuario == "alopez"
    assert usuario.cedula == 23456789


def test_rechazo_cedula_duplicada(patch_conexion):
    """Verifica que no se permita registrar dos usuarios con la misma cédula."""
    dao = UsuarioDAO()
    u1 = UsuarioCreate(
        nombre="Usuario",
        apellido="Uno",
        cedula=11112222,
        usuario="usuario1",
        clave="clave1",
    )
    u2 = UsuarioCreate(
        nombre="Usuario",
        apellido="Dos",
        cedula=11112222,
        usuario="usuario2",
        clave="clave2",
    )

    id1 = dao.crear(u1)
    assert id1 > 0

    id2 = dao.crear(u2)
    assert id2 == -1


def test_rechazo_usuario_duplicado(patch_conexion):
    """Verifica que no se permita registrar dos operadores con el mismo username."""
    dao = UsuarioDAO()
    u1 = UsuarioCreate(
        nombre="Operador",
        apellido="A",
        cedula=33334444,
        usuario="operador",
        clave="claveA",
    )
    u2 = UsuarioCreate(
        nombre="Operador",
        apellido="B",
        cedula=55556666,
        usuario="operador",
        clave="claveB",
    )

    id1 = dao.crear(u1)
    assert id1 > 0

    id2 = dao.crear(u2)
    assert id2 == -1


def test_validar_credenciales_correctas(usuario_semilla):
    """Verifica la autenticación exitosa con usuario y clave correctos."""
    dao = UsuarioDAO()
    usuario = dao.validar_credenciales("jperez", "clave123")

    assert usuario is not None
    assert isinstance(usuario, Usuario)
    assert usuario.id == usuario_semilla["id"]
    assert usuario.usuario == "jperez"


def test_validar_credenciales_incorrectas(usuario_semilla):
    """Verifica que una clave incorrecta no autentique y retorne None."""
    dao = UsuarioDAO()
    assert dao.validar_credenciales("jperez", "clave_erronea") is None


def test_validar_credenciales_usuario_inexistente(patch_conexion):
    """Verifica que un nombre de usuario inexistente retorne None."""
    dao = UsuarioDAO()
    assert dao.validar_credenciales("no_existe", "clave123") is None


def test_cambiar_clave_exitoso(usuario_semilla):
    """Verifica el cambio de clave proporcionando la contraseña actual correcta."""
    dao = UsuarioDAO()
    exito, msg = dao.cambiar_clave(
        usuario_semilla["id"], "clave123", "nuevaClave456"
    )
    assert exito is True
    assert "exitosamente" in msg.lower()

    # Verificar que la nueva clave es la que autentica
    assert dao.validar_credenciales("jperez", "nuevaClave456") is not None
    assert dao.validar_credenciales("jperez", "clave123") is None


def test_cambiar_clave_actual_incorrecta(usuario_semilla):
    """Verifica el rechazo del cambio de clave si la contraseña actual no coincide."""
    dao = UsuarioDAO()
    exito, msg = dao.cambiar_clave(
        usuario_semilla["id"], "clave_falsa", "nuevaClave456"
    )
    assert exito is False
    assert "incorrecta" in msg.lower()

    # La contraseña original debe seguir vigente
    assert dao.validar_credenciales("jperez", "clave123") is not None


def test_resetear_clave(usuario_semilla):
    """Verifica el reseteo administrativo de contraseña sin requerir la actual."""
    dao = UsuarioDAO()
    exito = dao.resetear_clave(usuario_semilla["id"], "claveReseteada789")
    assert exito is True

    # Comprobar que se puede iniciar sesión con la nueva contraseña
    usuario = dao.validar_credenciales("jperez", "claveReseteada789")
    assert usuario is not None
    assert usuario.id == usuario_semilla["id"]


def test_soft_delete_usuario(usuario_semilla):
    """Verifica que un usuario desactivado no pueda autenticarse ni recuperarse."""
    dao = UsuarioDAO()
    exito = dao.soft_delete(usuario_semilla["id"])
    assert exito is True

    # El usuario desactivado no debe autenticar
    assert dao.validar_credenciales("jperez", "clave123") is None
    # Tampoco debe recuperarse por id
    assert dao.obtener_por_id(usuario_semilla["id"]) is None


def test_obtener_por_usuario(usuario_semilla):
    """Verifica la recuperación de un usuario por su nombre de usuario (para preguntas de seguridad)."""
    dao = UsuarioDAO()
    usuario = dao.obtener_por_usuario("jperez")

    assert usuario is not None
    assert usuario.id == usuario_semilla["id"]
    assert usuario.usuario == "jperez"
    assert usuario.pregunta1 == "¿Color favorito?"
    assert usuario.respuesta1 == "azul"
