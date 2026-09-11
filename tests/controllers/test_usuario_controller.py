"""
Pruebas unitarias para UsuarioController (Controlador de Usuarios).

Verifica la orquestación del CRUD de operadores, validación Pydantic,
reglas de preguntas y respuestas de seguridad, unicidad de cédula/usuario,
cambio seguro de contraseñas y desactivación (soft delete).
"""

import pytest
from controllers.usuario_controller import UsuarioController
from models.usuario import Usuario


@pytest.fixture
def datos_usuario_validos():
    """Retorna un diccionario con datos válidos para registrar un usuario."""
    return {
        "nombre": "Carlos",
        "apellido": "Mendoza",
        "cedula": 18234567,
        "usuario": "cmendoza",
        "clave": "claveSegura123",
        "pregunta1": "¿Primer colegio?",
        "respuesta1": "San Jose",
        "pregunta2": "¿Color favorito?",
        "respuesta2": "Verde",
        "pregunta3": "¿Nombre de abuela?",
        "respuesta3": "Carmen",
    }


def test_registrar_usuario_exitoso(patch_conexion, datos_usuario_validos):
    """Verifica el registro exitoso de un nuevo usuario."""
    controller = UsuarioController()
    exito, mensaje = controller.registrar_usuario(datos_usuario_validos)

    assert exito is True
    assert "Usuario registrado exitosamente" in mensaje

    # Verificar que el usuario exista en la lista
    usuarios = controller.listar_usuarios()
    assert any(u.usuario == "cmendoza" for u in usuarios)


def test_registrar_usuario_faltan_preguntas_seguridad(patch_conexion, datos_usuario_validos):
    """Verifica que se rechace el registro si faltan preguntas o respuestas de seguridad."""
    controller = UsuarioController()

    # Falta pregunta 1
    datos_sin_p1 = datos_usuario_validos.copy()
    datos_sin_p1["pregunta1"] = ""
    exito, msg = controller.registrar_usuario(datos_sin_p1)
    assert exito is False
    assert "Pregunta de seguridad 1 es obligatoria" in msg

    # Falta respuesta 2
    datos_sin_r2 = datos_usuario_validos.copy()
    datos_sin_r2["respuesta2"] = "   "
    exito, msg = controller.registrar_usuario(datos_sin_r2)
    assert exito is False
    assert "Respuesta de seguridad 2 es obligatoria" in msg


def test_registrar_usuario_error_validacion_pydantic(patch_conexion, datos_usuario_validos):
    """Verifica que se capturen los errores de validación del modelo Pydantic (campo faltante)."""
    controller = UsuarioController()
    datos_invalidos = datos_usuario_validos.copy()
    del datos_invalidos["nombre"]

    exito, msg = controller.registrar_usuario(datos_invalidos)
    assert exito is False
    assert "Errores de validacion:" in msg


def test_registrar_usuario_cedula_o_nombre_duplicado(patch_conexion, datos_usuario_validos):
    """Verifica que no se permita registrar dos usuarios con la misma cédula o nombre de usuario."""
    controller = UsuarioController()

    # Primer registro
    exito, _ = controller.registrar_usuario(datos_usuario_validos)
    assert exito is True

    # Intento con el mismo usuario y cédula
    exito2, msg2 = controller.registrar_usuario(datos_usuario_validos)
    assert exito2 is False
    assert "Ya existe un usuario con esa cedula o nombre de usuario" in msg2

    # Intento con misma cédula pero diferente username
    datos_misma_cedula = datos_usuario_validos.copy()
    datos_misma_cedula["usuario"] = "otrousuario"
    exito3, msg3 = controller.registrar_usuario(datos_misma_cedula)
    assert exito3 is False
    assert "Ya existe un usuario" in msg3


def test_listar_usuarios(usuario_semilla):
    """Verifica que listar_usuarios devuelva los operadores activos."""
    controller = UsuarioController()
    usuarios = controller.listar_usuarios()

    assert len(usuarios) >= 1
    assert any(u.id == usuario_semilla["id"] for u in usuarios)
    assert all(isinstance(u, Usuario) for u in usuarios)


def test_obtener_usuario_existente(usuario_semilla):
    """Verifica la recuperación de un usuario por su ID."""
    controller = UsuarioController()
    exito, usuario = controller.obtener_usuario(usuario_semilla["id"])

    assert exito is True
    assert isinstance(usuario, Usuario)
    assert usuario.usuario == usuario_semilla["usuario"]
    assert usuario.cedula == usuario_semilla["cedula"]


def test_obtener_usuario_inexistente(patch_conexion):
    """Verifica el manejo de error al consultar un ID que no existe."""
    controller = UsuarioController()
    exito, msg = controller.obtener_usuario(99999)

    assert exito is False
    assert "Usuario no encontrado o inactivo" in msg


def test_actualizar_usuario_exitoso(usuario_semilla):
    """Verifica la actualización correcta de los datos de un usuario."""
    controller = UsuarioController()
    datos_actualizados = {
        "nombre": "Juan Carlos",
        "apellido": "Pérez Modificado",
        "cedula": usuario_semilla["cedula"],
        "usuario": usuario_semilla["usuario"],
        "clave": "nuevaClave123",
        "pregunta1": "¿Color?",
        "respuesta1": "Rojo",
        "pregunta2": "¿Mascota?",
        "respuesta2": "Gato",
        "pregunta3": "¿Ciudad?",
        "respuesta3": "Valencia",
    }

    exito, msg = controller.actualizar_usuario(usuario_semilla["id"], datos_actualizados)
    assert exito is True
    assert "Usuario actualizado exitosamente" in msg

    # Comprobar los cambios
    _, usuario = controller.obtener_usuario(usuario_semilla["id"])
    assert usuario.nombre == "Juan Carlos"
    assert usuario.apellido == "Pérez Modificado"


def test_actualizar_usuario_preguntas_invalidas(usuario_semilla):
    """Verifica que se rechace la actualización si las preguntas de seguridad son incompletas."""
    controller = UsuarioController()
    datos_invalidos = {
        "nombre": "Juan",
        "apellido": "Pérez",
        "cedula": usuario_semilla["cedula"],
        "usuario": usuario_semilla["usuario"],
        "clave": "clave123",
        "pregunta1": "",
        "respuesta1": "",
        "pregunta2": "¿Mascota?",
        "respuesta2": "perro",
        "pregunta3": "¿Ciudad?",
        "respuesta3": "caracas",
    }

    exito, msg = controller.actualizar_usuario(usuario_semilla["id"], datos_invalidos)
    assert exito is False
    assert "Errores de validacion:" in msg
    assert "Pregunta de seguridad 1 es obligatoria" in msg


def test_actualizar_usuario_duplicado(patch_conexion, datos_usuario_validos, usuario_semilla):
    """Verifica que no se pueda actualizar un usuario asignándole la cédula o username de otro."""
    controller = UsuarioController()

    # Registrar un segundo usuario
    controller.registrar_usuario(datos_usuario_validos)
    _, user2 = controller.obtener_usuario_por_filtro if hasattr(controller, "obtener_usuario_por_filtro") else (None, None)
    usuarios = controller.listar_usuarios()
    user2 = next(u for u in usuarios if u.usuario == datos_usuario_validos["usuario"])

    # Intentar actualizar user2 con la cédula de usuario_semilla
    datos_duplicados = datos_usuario_validos.copy()
    datos_duplicados["cedula"] = usuario_semilla["cedula"]

    exito, msg = controller.actualizar_usuario(user2.id, datos_duplicados)
    assert exito is False
    assert "No se pudo actualizar" in msg


def test_eliminar_usuario_exitoso(usuario_semilla):
    """Verifica el borrado lógico de un usuario."""
    controller = UsuarioController()
    exito, msg = controller.eliminar_usuario(usuario_semilla["id"])

    assert exito is True
    assert "Usuario desactivado exitosamente" in msg

    # Ya no debe aparecer en obtener_usuario
    exito_get, _ = controller.obtener_usuario(usuario_semilla["id"])
    assert exito_get is False


def test_eliminar_usuario_inexistente(patch_conexion):
    """Verifica el manejo de error al intentar desactivar un usuario inexistente."""
    controller = UsuarioController()
    exito, msg = controller.eliminar_usuario(99999)

    assert exito is False
    assert "No se pudo desactivar el usuario" in msg


def test_cambiar_clave_validaciones(usuario_semilla):
    """Verifica las validaciones de cambio de contraseña en UsuarioController."""
    controller = UsuarioController()
    id_u = usuario_semilla["id"]
    clave_act = usuario_semilla["clave"]

    # Clave actual vacía
    exito, msg = controller.cambiar_clave(id_u, "", "nueva123", "nueva123")
    assert exito is False
    assert "Debe ingresar la contraseña actual" in msg

    # Nueva clave vacía
    exito, msg = controller.cambiar_clave(id_u, clave_act, "   ", "   ")
    assert exito is False
    assert "Debe ingresar la nueva contraseña" in msg

    # Nueva clave menor a 4 caracteres
    exito, msg = controller.cambiar_clave(id_u, clave_act, "123", "123")
    assert exito is False
    assert "al menos 4 caracteres" in msg

    # Confirmación no coincide
    exito, msg = controller.cambiar_clave(id_u, clave_act, "nueva123", "otraClave")
    assert exito is False
    assert "no coinciden" in msg

    # Clave actual incorrecta
    exito, msg = controller.cambiar_clave(id_u, "claveErronea", "nueva123", "nueva123")
    assert exito is False
    assert "incorrecta" in msg

    # Cambio exitoso
    exito, msg = controller.cambiar_clave(id_u, clave_act, "nueva123", "nueva123")
    assert exito is True
    assert "exitosamente" in msg
