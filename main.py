
import sys
import os
import sqlite3
import threading
from datetime import datetime, timedelta

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SRC_DIR = os.path.join(BASE_DIR, "src")
sys.path.insert(0, SRC_DIR)

import customtkinter as ctk
from views.dashboard_view import DashboardView
from views.login_view import LoginView
from utils.logging_config import inicializar_logs

# pyrefly: ignore [missing-import]
# pyrefly: ignore [missing-import]
# pyrefly: ignore [missing-import]


# ── Rutas de la base de datos ─────────────────────────────────────
DB_PATH = os.path.join(BASE_DIR, "database", "database.db")
SQL_PATH = os.path.join(BASE_DIR, "database", "schema.sql")


def inicializar_db():
    """Crea el directorio de la base de datos si no existe
    y ejecuta el esquema SQL para crear las tablas.
    Tolera objetos ya existentes (tablas, vistas, índices).
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if os.path.exists(SQL_PATH):
        with open(SQL_PATH, "r", encoding="utf-8") as f:
            sql = f.read()
        try:
            cursor.executescript(sql)
            print(f"[OK] Esquema cargado desde: {SQL_PATH}")
        except sqlite3.OperationalError as e:
            if "already exists" in str(e):
                print(f"[OK] Esquema ya existente, continuando.")
            else:
                raise
    else:
        print(
            f"[ADVERTENCIA] No se encontro el archivo de esquema: {SQL_PATH}")

    conn.close()


# ── Hilo de backup programado ────────────────────────────────────

def _hilo_backup_programado(stop_event: threading.Event):
    """Hilo daemon que verifica cada 30 s si es hora de hacer backup.

    Lee la configuración desde disco en cada ciclo para reflejar
    cambios realizados por el usuario sin reiniciar la app.
    """
    from loguru import logger

    while not stop_event.is_set():
        stop_event.wait(30)  # Duerme 30 s o se despierta si stop
        if stop_event.is_set():
            break
        try:
            from models.config import cargar_config, guardar_config

            config = cargar_config()
            if not config.backup_programado_habilitado:
                continue

            ahora = datetime.now()
            hoy = ahora.strftime("%Y-%m-%d")
            if config.backup_ultimo_dia_ejecutado == hoy:
                continue  # Ya se ejecutó hoy

            partes = config.backup_programado_hora.split(":")
            hora_prog = int(partes[0]) if len(partes) == 2 else 23
            min_prog = int(partes[1]) if len(partes) == 2 else 0

            if ahora.hour == hora_prog and ahora.minute >= min_prog:
                logger.info("Iniciando backup programado...")
                from utils.backup_service import (
                    realizar_backup_local,
                    subir_a_google_drive,
                    limpiar_backups_antiguos,
                )

                exito, resultado = realizar_backup_local()
                if exito:
                    logger.info(f"Backup programado creado: {resultado}")
                    limpiar_backups_antiguos(10)

                    # Subir a la nube si está habilitado
                    if (config.backup_nube_habilitado
                            and config.backup_drive_folder_id):
                        ok, msg = subir_a_google_drive(
                            resultado, config.backup_drive_folder_id)
                        if ok:
                            logger.info(f"Backup programado subido a Drive: {msg}")
                        else:
                            logger.warning(f"Error al subir backup programado a Drive: {msg}")
                else:
                    logger.warning(f"Error en backup programado: {resultado}")

                # Marcar como ejecutado hoy
                config.backup_ultimo_dia_ejecutado = hoy
                guardar_config(config)
        except Exception as e:
            from loguru import logger as _log
            _log.error(f"Error en hilo de backup programado: {e}")


class App:
    """Clase principal de la aplicación.
    Gestiona el ciclo de vida de las ventanas (Login ↔ Dashboard).
    """

    def __init__(self):
        # ── Configuración global de CustomTkinter ──
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # ── Ventana raíz (oculta, solo sirve como master) ──
        self.root = ctk.CTk()
        self.root.withdraw()

        # Configurar selección de texto legible (fuente blanca sobre acento azul) globalmente
        self.root.option_add("*Entry.selectForeground", "white")
        self.root.option_add("*Entry.selectBackground", "#0078D4")

        # Referencia a las ventanas activas
        self.login_view = None
        self.dashboard_view = None

        # Evento para detener el hilo de backup al cerrar
        self._stop_backup = threading.Event()

    def iniciar(self):
        """Punto de arranque: muestra el login y lanza el mainloop."""
        # Lanzar hilo de backup programado
        hilo = threading.Thread(
            target=_hilo_backup_programado,
            args=(self._stop_backup,),
            daemon=True,
        )
        hilo.start()

        self._mostrar_login()
        self.root.mainloop()

        # Señalar al hilo que termine
        self._stop_backup.set()

    def _mostrar_login(self):
        """Crea y muestra la ventana de inicio de sesión."""
        self.login_view = LoginView(
            master=self.root,
            on_login_success=self._on_login_exitoso,
        )

    def _on_login_exitoso(self, usuario):
        """Callback que se ejecuta al autenticarse correctamente.
        Cierra el login y abre el dashboard.
        """
        self.login_view = None
        self.dashboard_view = DashboardView(
            master=self.root,
            usuario=usuario,
            on_logout=self._on_logout,
        )

    def _on_logout(self):
        """Callback que se ejecuta al cerrar sesión.
        Destruye el dashboard y vuelve a mostrar el login.
        """
        self.dashboard_view = None
        self._mostrar_login()


# ── Entry Point ──────────────────────────────────────────────────
if __name__ == "__main__":
    inicializar_logs()
    inicializar_db()
    app = App()
    app.iniciar()

