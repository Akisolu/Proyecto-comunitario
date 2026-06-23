"""
Modelo de configuración del sistema SGI Salud.

Gestiona las preferencias del usuario (tema, fuente, modo de N. Historia)
y las persiste en un archivo JSON local en `database/config.json`.

Uso:
    from models.config import cargar_config, guardar_config

    config = cargar_config()          # Lee o crea config por defecto
    config.tema = "claro"
    guardar_config(config)            # Persiste en disco
"""

import os
import json
from pydantic import BaseModel, Field


# ── Ruta del archivo de configuración ─────────────────────────────
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(_BASE_DIR, "database", "config.json")


# ── Valores válidos ───────────────────────────────────────────────
TEMAS_VALIDOS = ("oscuro", "claro", "personalizado")
TAMANOS_FUENTE_VALIDOS = ("pequeno", "normal", "grande", "muy_grande")
MODOS_HISTORIA_VALIDOS = ("manual", "auto")


class ColoresPersonalizados(BaseModel):
    """Colores definidos por el usuario para el tema 'personalizado'.

    Atributos:
        fondo:           Color de fondo general de la app.
        panel:           Color de paneles, tarjetas y contenedores.
        acento:          Color principal de botones y acentos.
        acento_hover:    Color de botones al pasar el cursor.
        texto:           Color del texto principal.
        texto_secundario: Color del texto de baja prioridad.
        entrada_fondo:   Fondo de campos de texto (inputs).
        entrada_borde:   Borde de campos de texto.
        error:           Color de mensajes de error.
        exito:           Color de mensajes de éxito.
        peligro:         Color de botón eliminar.
        fila_alterna:    Color de filas alternas en tablas.
    """
    fondo: str = "#0F1923"
    panel: str = "#182633"
    acento: str = "#00A8E8"
    acento_hover: str = "#007BB5"
    texto: str = "#E8EDF2"
    texto_secundario: str = "#8899AA"
    entrada_fondo: str = "#1E3044"
    entrada_borde: str = "#2A4158"
    error: str = "#FF4C6A"
    exito: str = "#00D68F"
    peligro: str = "#FF4C6A"
    peligro_hover: str = "#D93A5A"
    fila_alterna: str = "#1A2D3D"


class AppConfig(BaseModel):
    """Configuración general de la aplicación.

    Atributos:
        tema:              Tema visual. Opciones: 'oscuro', 'claro', 'personalizado'.
        tamano_fuente:     Tamaño de fuente. Opciones: 'pequeno', 'normal', 'grande', 'muy_grande'.
        modo_num_historia: Modo de ingreso del N. de Historia. Opciones: 'manual', 'auto'.
        colores_personalizados: Colores del tema personalizado (solo aplica si tema='personalizado').

        backup_al_cerrar:              Si True, genera respaldo automático al cerrar la app.
        backup_programado_habilitado:  Si True, habilita el respaldo programado diario.
        backup_programado_hora:        Hora del respaldo programado en formato 'HH:MM'.
        backup_nube_habilitado:        Si True, sube los respaldos a Google Drive.
        backup_drive_folder_id:        ID de la carpeta de Google Drive destino.
        backup_ultimo_dia_ejecutado:   Fecha (YYYY-MM-DD) del último respaldo programado.
    """
    tema: str = Field(default="oscuro")
    tamano_fuente: str = Field(default="normal")
    modo_num_historia: str = Field(default="manual")
    registros_por_pagina: int = Field(default=20)
    colores_personalizados: ColoresPersonalizados = Field(
        default_factory=ColoresPersonalizados
    )

    # ── Copias de Seguridad ──
    backup_al_cerrar: bool = Field(default=True)
    backup_programado_habilitado: bool = Field(default=False)
    backup_programado_hora: str = Field(default="23:00")
    backup_nube_habilitado: bool = Field(default=False)
    backup_drive_folder_id: str = Field(default="")
    backup_ultimo_dia_ejecutado: str = Field(default="")


def cargar_config() -> AppConfig:
    """Lee la configuración desde el archivo JSON.

    Si el archivo no existe o está corrupto, retorna la configuración
    por defecto y la guarda automáticamente.

    Returns:
        AppConfig con las preferencias del usuario.
    """
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as archivo:
                datos = json.load(archivo)
            return AppConfig(**datos)
        except (json.JSONDecodeError, Exception):
            pass  # Archivo corrupto → usar defaults

    # No existe o está corrupto: crear con defaults
    config = AppConfig()
    guardar_config(config)
    return config


def guardar_config(config: AppConfig) -> None:
    """Persiste la configuración en el archivo JSON.

    Crea el directorio si no existe.

    Args:
        config: Objeto AppConfig a guardar.
    """
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as archivo:
        json.dump(config.model_dump(), archivo, indent=2, ensure_ascii=False)
