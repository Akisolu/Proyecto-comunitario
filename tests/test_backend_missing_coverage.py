"""Cobertura extra para controladores y DAO con SQLite en memoria.

Incluye pruebas para:
- UsuarioController: registro, actualización, cambio de clave y desactivación.
- BusquedaController/BusquedaDAO: paginación, conteo total y filtros.
- ColorController/ColorDAO: CRUD del catálogo cromático.
- ConexionDB: validación de ruta y manejo de errores.
"""

import os
import sqlite3

import pytest

from controllers.busqueda_controller import BusquedaController
from controllers.color_controller import ColorController
from controllers.usuario_controller import UsuarioController
from dao.busqueda import BusquedaDAO
from dao.color import ColorDAO
from dao.conexion import ConexionDB
from models.busqueda import TarjetaSalida
from models.color import Color, ColorBase
from models.num_historia_utils import obtener_color_por_num_historia
from models.paciente import PacienteCreate
from models.tarjeta import TarjetaCreate
from models.usuario import Usuario


@pytest.fixture
def usuario_datos_validos():
    return {
        "nombre": "Ana",
        "apellido": "López",
        "cedula": 30123456,
        "usuario": "alopez",
        "clave": "clave123",
        "pregunta1": "¿Color favorito?",
        "respuesta1": "Azul",
        "pregunta2": "¿Mascota?",
        "respuesta2": "Perro",
        "pregunta3": "¿Ciudad natal?",
        "respuesta3": "Caracas",
    }


def _crear_paciente_tarjeta(patch_conexion, cedula, nombre, apellido, num_historia, fecha="15/05/1990", lugar="Turén"):
    from dao.paciente import PacienteDAO
    from dao.tarjeta import TarjetaDAO

    paciente_dao = PacienteDAO()
    tarjeta_dao = TarjetaDAO()
    color_dao = ColorDAO()

    paciente = PacienteCreate(
        cedula=f"V-{cedula}",
        nombre1=nombre,
        apellido1=apellido,
        fecha_nacimiento=fecha,
        lugar_nacimiento=lugar,
        estado_vital=1,
    )
    id_paciente = paciente_dao.crear(paciente)

    info = obtener_color_por_num_historia(num_historia)
    color = color_dao.obtener_por_valor(info["nombre"])
    assert color is not None

    tarjeta = TarjetaCreate(
        num_historia=num_historia,
        id_paciente=id_paciente,
        id_color=color.id,
    )
    tarjeta_dao.crear(tarjeta)
    return id_paciente


class TestUsuarioController:
    def test_registrar_usuario_exitoso(self, patch_conexion, usuario_datos_validos):
        controller = UsuarioController()

        ok, msg = controller.registrar_usuario(usuario_datos_validos)

        assert ok is True
        assert "Usuario registrado exitosamente" in msg
        assert any(u.usuario == "alopez" for u in controller.listar_usuarios())

    def test_registrar_usuario_invalidos_y_duplicados(self, patch_conexion, usuario_datos_validos):
        controller = UsuarioController()

        datos_invalidos = usuario_datos_validos.copy()
        datos_invalidos["pregunta1"] = ""
        ok, msg = controller.registrar_usuario(datos_invalidos)
        assert ok is False
        assert "Pregunta de seguridad 1 es obligatoria" in msg

        datos_pydantic = usuario_datos_validos.copy()
        del datos_pydantic["nombre"]
        ok, msg = controller.registrar_usuario(datos_pydantic)
        assert ok is False
        assert "Errores de validacion:" in msg

        ok, _ = controller.registrar_usuario(usuario_datos_validos)
        assert ok is True

        duplicado = usuario_datos_validos.copy()
        duplicado["usuario"] = "otro_usuario"
        ok, msg = controller.registrar_usuario(duplicado)
        assert ok is False
        assert "Ya existe un usuario con esa cedula o nombre de usuario" in msg

    def test_actualizar_usuario_exitoso_y_duplicado(self, patch_conexion, usuario_datos_validos):
        controller = UsuarioController()
        ok, _ = controller.registrar_usuario(usuario_datos_validos)
        assert ok is True

        usuario = controller.listar_usuarios()[0]
        datos = {
            "nombre": "Ana M.",
            "apellido": "López Cruz",
            "cedula": usuario.cedula,
            "usuario": usuario.usuario,
            "clave": "nuevaClave123",
            "pregunta1": "¿Color favorito?",
            "respuesta1": "Verde",
            "pregunta2": "¿Mascota?",
            "respuesta2": "Gato",
            "pregunta3": "¿Ciudad natal?",
            "respuesta3": "Valencia",
        }

        ok, msg = controller.actualizar_usuario(usuario.id, datos)
        assert ok is True
        assert "Usuario actualizado exitosamente" in msg

        segundo = usuario_datos_validos.copy()
        segundo["usuario"] = "segsuario"
        segundo["cedula"] = 50000000
        ok, _ = controller.registrar_usuario(segundo)
        assert ok is True

        conflicto = {
            **datos,
            "cedula": 50000000,
            "usuario": "segsuario",
        }
        ok, msg = controller.actualizar_usuario(usuario.id, conflicto)
        assert ok is False
        assert "No se pudo actualizar" in msg

    def test_cambiar_clave_y_desactivar_usuario(self, patch_conexion, usuario_datos_validos):
        controller = UsuarioController()
        ok, _ = controller.registrar_usuario(usuario_datos_validos)
        assert ok is True

        usuario = controller.listar_usuarios()[0]

        ok, msg = controller.cambiar_clave(usuario.id, "clave123", "nueva1234", "nueva1234")
        assert ok is True
        assert "Contraseña actualizada exitosamente" in msg

        ok, msg = controller.cambiar_clave(usuario.id, "clave123", "otra1234", "otra1234")
        assert ok is False
        assert "incorrecta" in msg

        ok, msg = controller.eliminar_usuario(usuario.id)
        assert ok is True
        assert "Usuario desactivado exitosamente" in msg

        ok, msg = controller.obtener_usuario(usuario.id)
        assert ok is False
        assert "Usuario no encontrado o inactivo" in msg


class TestBusquedaControllerYDAO:
    def test_busqueda_controller_datos_validos_y_criterio_invalido(self, paciente_con_tarjeta):
        controller = BusquedaController()

        ok, value = controller.buscar("todos", "")
        assert ok is True
        assert isinstance(value, tuple)
        registros, total = value
        assert total >= 1
        assert len(registros) >= 1
        assert isinstance(registros[0], TarjetaSalida)

        ok, msg = controller.buscar("criterio_invalido", "maría")
        assert ok is False
        assert "Criterio de búsqueda no válido" in msg

    def test_busqueda_dao_paginacion_y_totales(self, patch_conexion):
        _crear_paciente_tarjeta(patch_conexion, "10000001", "María", "García", "10-10-10")
        _crear_paciente_tarjeta(patch_conexion, "10000002", "Luis", "Pérez", "20-20-20")
        _crear_paciente_tarjeta(patch_conexion, "10000003", "Ana", "Torres", "30-30-30")

        dao = BusquedaDAO()
        pagina_1, total_1 = dao.obtener_todos(limit=2, offset=0)
        pagina_2, total_2 = dao.obtener_todos(limit=2, offset=2)

        assert total_1 == 3
        assert total_2 == 3
        assert len(pagina_1) == 2
        assert len(pagina_2) == 1
        assert {p.id_paciente for p in pagina_1}.isdisjoint({p.id_paciente for p in pagina_2})

    def test_busqueda_por_cedula_nombre_y_num_historia(self, paciente_con_tarjeta):
        dao = BusquedaDAO()

        resultados, total = dao.buscar_por_cedula("12345")
        assert total == 1
        assert resultados[0].cedula == "V-12345678"

        resultados, total = dao.buscar_por_nombre("María")
        assert total == 1
        assert resultados[0].nombre1 == "María"

        resultados, total = dao.buscar_por_num_historia("03-77")
        assert total == 1
        assert resultados[0].num_historia == "03-77-34"

    def test_busqueda_sin_coincidencias(self, paciente_con_tarjeta):
        dao = BusquedaDAO()

        for metodo, valor in [
            (dao.buscar_por_cedula, "NOEXISTE"),
            (dao.buscar_por_nombre, "Nadie"),
            (dao.buscar_por_num_historia, "99-99-99"),
        ]:
            resultados, total = metodo(valor)
            assert total == 0
            assert resultados == []

    def test_busqueda_multicriterio_y_excepcion(self, paciente_con_tarjeta, monkeypatch):
        controller = BusquedaController()

        ok, value = controller.buscar_multicriterio({"nombre": "María", "apellido": "González", "lugar_nacimiento": "Turén"})
        assert ok is True
        registros, total = value
        assert total == 1
        assert registros[0].id_paciente == paciente_con_tarjeta["id"]

        def _raise(*args, **kwargs):
            raise RuntimeError("Fallo simulado de DAO")

        monkeypatch.setattr(controller.busqueda_dao, "buscar_multicriterio", _raise)
        ok, msg = controller.buscar_multicriterio({"cedula": "1234"})
        assert ok is False
        assert "Error al realizar la búsqueda multi-criterio" in msg


class TestColorControllerYDAO:
    def test_color_controller_listar_y_obtener(self, patch_conexion):
        controller = ColorController()

        colores = controller.listar_colores()
        assert len(colores) == 10
        assert all(isinstance(c, Color) for c in colores)

        color = controller.obtener_color(colores[0].id)
        assert color is not None
        assert color.id == colores[0].id

        assert controller.obtener_color(999999) is None

    def test_color_dao_crud_completo(self, patch_conexion):
        dao = ColorDAO()
        nuevo = ColorBase(valor="Dorado")
        id_color = dao.crear(nuevo)
        assert id_color > 0

        color = dao.obtener_por_id(id_color)
        assert color is not None and color.valor == "Dorado"

        ok = dao.actualizar(id_color, ColorBase(valor="Oro"))
        assert ok is True
        assert dao.obtener_por_id(id_color).valor == "Oro"

        ok = dao.soft_delete(id_color)
        assert ok is True
        assert dao.obtener_por_id(id_color) is None
        assert dao.obtener_por_valor("Oro") is None

        assert all(c.id != id_color for c in dao.obtener_todos())


class TestConexionDB:
    def test_conexion_db_ruta_por_defecto_y_personalizada(self, tmp_path):
        db_default = ConexionDB()
        assert db_default.db_path.endswith(os.path.join("database", "database.db"))

        ruta = str(tmp_path / "subdir" / "mi_bd.sqlite")
        db_custom = ConexionDB(ruta)
        assert db_custom.db_path == ruta

    def test_obtener_conexion_crea_directorio(self, tmp_path):
        ruta = str(tmp_path / "carpeta" / "db" / "hospital.db")
        db = ConexionDB(ruta)

        conn = db.obtener_conexion()
        assert os.path.exists(os.path.dirname(ruta))
        assert isinstance(conn, object)
        conn.close()

    def test_obtener_conexion_errores_y_validacion(self, tmp_path, monkeypatch):
        db = ConexionDB(str(tmp_path / "sin_permiso" / "db.sqlite"))

        def _fake_makedirs(*args, **kwargs):
            raise PermissionError("Acceso denegado")

        monkeypatch.setattr(os, "makedirs", _fake_makedirs)
        with pytest.raises(PermissionError, match="Acceso denegado"):
            db.obtener_conexion()
        monkeypatch.undo()

        def _fake_connect(*args, **kwargs):
            raise sqlite3.OperationalError("unable to open database file")

        monkeypatch.setattr(sqlite3, "connect", _fake_connect)
        with pytest.raises(sqlite3.OperationalError, match="unable to open database file"):
            ConexionDB(str(tmp_path / "mal" / "db.sqlite")).obtener_conexion()
