# -*- coding: utf-8 -*-
"""Servicio de respaldo para el sistema SGI Salud.

Este módulo centraliza todas las operaciones de respaldo de la base de datos
del sistema hospitalario, incluyendo:

- Copias de seguridad locales (database.db → backups/backup_YYYYMMDD_HHMMSS.db)
- Subida de respaldos a Google Drive mediante Cuenta de Servicio
- Encriptación y desencriptación de credenciales sensibles con Fernet
- Limpieza automática de respaldos antiguos
"""

from __future__ import annotations

import base64
import hashlib
import os
import shutil
from datetime import datetime

from loguru import logger

# ---------------------------------------------------------------------------
# Rutas base del proyecto (relativas a la ubicación de este archivo)
# src/utils/backup_service.py  →  src/utils  →  src  →  raíz del proyecto
# ---------------------------------------------------------------------------
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(_BASE_DIR, "database", "database.db")
BACKUPS_DIR = os.path.join(_BASE_DIR, "backups")
CREDENTIALS_PATH = os.path.join(_BASE_DIR, "database", "google_credentials.json")


# ═══════════════════════════════════════════════════════════════════════════
# Encriptación de credenciales
# ═══════════════════════════════════════════════════════════════════════════

def _obtener_clave_maquina() -> bytes:
    """Genera una clave Fernet determinística basada en el entorno de la máquina.

    La clave se deriva del nombre del equipo, el usuario del sistema operativo
    y una sal fija del proyecto. Esto garantiza que los valores encriptados
    solo puedan ser desencriptados en la misma máquina y sesión de usuario
    donde fueron creados.

    Returns:
        bytes: Clave de 32 bytes codificada en URL-safe base64, compatible
               con ``cryptography.fernet.Fernet``.
    """
    import platform

    semilla = (
        f"{platform.node()}-"
        f"{os.getenv('USERNAME', os.getenv('USER', 'default'))}-"
        f"SGISalud"
    )
    hash_bytes = hashlib.sha256(semilla.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(hash_bytes)


def encriptar_valor(texto_plano: str) -> str:
    """Encripta un string usando Fernet con la clave de máquina.

    Args:
        texto_plano: Texto en claro a encriptar.

    Returns:
        Cadena cifrada codificada en base64. Si el texto de entrada está
        vacío, retorna una cadena vacía.
    """
    if not texto_plano:
        return ""

    from cryptography.fernet import Fernet

    f = Fernet(_obtener_clave_maquina())
    return f.encrypt(texto_plano.encode("utf-8")).decode("utf-8")


def desencriptar_valor(texto_cifrado: str) -> str:
    """Desencripta un string previamente cifrado con :func:`encriptar_valor`.

    Args:
        texto_cifrado: Cadena cifrada en base64.

    Returns:
        Texto plano original, o cadena vacía si la desencriptación falla
        (por ejemplo, clave incorrecta o datos corruptos).
    """
    if not texto_cifrado:
        return ""
    try:
        from cryptography.fernet import Fernet

        f = Fernet(_obtener_clave_maquina())
        return f.decrypt(texto_cifrado.encode("utf-8")).decode("utf-8")
    except Exception:
        logger.warning("No se pudo desencriptar el valor proporcionado.")
        return ""


# ═══════════════════════════════════════════════════════════════════════════
# Respaldo local
# ═══════════════════════════════════════════════════════════════════════════

def realizar_backup_local() -> tuple[bool, str]:
    """Crea una copia de seguridad local de la base de datos.

    Copia ``database.db`` al directorio ``backups/`` con un nombre que
    incluye la marca de tiempo actual en formato ``backup_YYYYMMDD_HHMMSS.db``.
    El directorio de respaldos se crea automáticamente si no existe.

    Returns:
        tuple[bool, str]: ``(True, ruta_del_backup)`` en caso de éxito, o
                          ``(False, mensaje_de_error)`` si ocurre algún fallo.
    """
    try:
        # Verificar que la base de datos origen exista
        if not os.path.exists(DB_PATH):
            mensaje = f"No se encontró la base de datos en: {DB_PATH}"
            logger.error(mensaje)
            return False, mensaje

        # Crear directorio de respaldos si no existe
        os.makedirs(BACKUPS_DIR, exist_ok=True)

        # Generar nombre con marca de tiempo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_backup = f"backup_{timestamp}.db"
        ruta_backup = os.path.join(BACKUPS_DIR, nombre_backup)

        # Copiar preservando metadatos
        shutil.copy2(DB_PATH, ruta_backup)

        logger.info(f"Backup local creado exitosamente: {ruta_backup}")
        return True, ruta_backup

    except PermissionError:
        mensaje = "Permiso denegado al intentar crear el respaldo local."
        logger.error(mensaje)
        return False, mensaje
    except Exception as e:
        mensaje = f"Error inesperado al crear backup local: {e}"
        logger.error(mensaje)
        return False, mensaje


# ═══════════════════════════════════════════════════════════════════════════
# Subida a Google Drive
# ═══════════════════════════════════════════════════════════════════════════

def subir_a_google_drive(ruta_archivo: str, folder_id: str) -> tuple[bool, str]:
    """Sube un archivo a Google Drive mediante una Cuenta de Servicio.

    Utiliza el archivo ``google_credentials.json`` ubicado en el directorio
    ``database/`` del proyecto para autenticarse. La subida se realiza en
    modo *resumable* para soportar archivos grandes de forma confiable.

    Requisitos:
        - ``google_credentials.json`` presente en ``database/``
        - Paquetes instalados: ``google-api-python-client``,
          ``google-auth-httplib2``, ``google-auth-oauthlib``

    Args:
        ruta_archivo: Ruta absoluta al archivo que se desea subir.
        folder_id: ID de la carpeta de Google Drive donde se subirá el archivo.

    Returns:
        tuple[bool, str]: ``(True, file_id)`` con el ID del archivo en Drive
                          si la subida fue exitosa, o ``(False, mensaje_error)``
                          en caso de fallo.
    """
    # Importar dependencias de Google de forma segura
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        mensaje = (
            "Las dependencias de Google Drive no están instaladas. "
            "Instale los paquetes: google-api-python-client, "
            "google-auth-httplib2, google-auth-oauthlib"
        )
        logger.error(mensaje)
        return False, mensaje

    try:
        # Validar que el archivo a subir exista
        if not os.path.exists(ruta_archivo):
            mensaje = f"El archivo a subir no existe: {ruta_archivo}"
            logger.error(mensaje)
            return False, mensaje

        # Validar que las credenciales existan
        if not verificar_credenciales_drive():
            mensaje = (
                f"No se encontró el archivo de credenciales en: "
                f"{CREDENTIALS_PATH}"
            )
            logger.error(mensaje)
            return False, mensaje

        # Autenticar con Cuenta de Servicio
        scopes = ["https://www.googleapis.com/auth/drive.file"]
        credenciales = service_account.Credentials.from_service_account_file(
            CREDENTIALS_PATH, scopes=scopes
        )
        servicio = build("drive", "v3", credentials=credenciales)

        # Preparar metadatos del archivo
        nombre_archivo = os.path.basename(ruta_archivo)
        file_metadata = {
            "name": nombre_archivo,
            "parents": [folder_id],
        }

        # Subir archivo en modo resumable
        media = MediaFileUpload(
            ruta_archivo,
            mimetype="application/octet-stream",
            resumable=True,
        )

        archivo = (
            servicio.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )

        file_id = archivo.get("id", "")
        logger.info(
            f"Archivo subido a Google Drive exitosamente. "
            f"Nombre: {nombre_archivo}, ID: {file_id}"
        )
        return True, file_id

    except Exception as e:
        mensaje = f"Error al subir archivo a Google Drive: {e}"
        logger.error(mensaje)
        return False, mensaje


# ═══════════════════════════════════════════════════════════════════════════
# Limpieza de respaldos antiguos
# ═══════════════════════════════════════════════════════════════════════════

def limpiar_backups_antiguos(max_backups: int = 10) -> int:
    """Elimina los respaldos locales más antiguos, conservando los más recientes.

    Ordena los archivos ``.db`` del directorio de respaldos por fecha de
    modificación y elimina los que excedan el límite especificado.

    Args:
        max_backups: Cantidad máxima de archivos de respaldo a conservar.
                     Por defecto se conservan los 10 más recientes.

    Returns:
        int: Cantidad de archivos de respaldo eliminados.
    """
    eliminados = 0

    try:
        if not os.path.exists(BACKUPS_DIR):
            logger.debug("El directorio de backups no existe, nada que limpiar.")
            return 0

        # Listar solo archivos .db del directorio de backups
        archivos = [
            os.path.join(BACKUPS_DIR, f)
            for f in os.listdir(BACKUPS_DIR)
            if f.endswith(".db") and os.path.isfile(os.path.join(BACKUPS_DIR, f))
        ]

        if len(archivos) <= max_backups:
            logger.debug(
                f"Hay {len(archivos)} backup(s), no se requiere limpieza "
                f"(máximo permitido: {max_backups})."
            )
            return 0

        # Ordenar por fecha de modificación (más recientes primero)
        archivos.sort(key=os.path.getmtime, reverse=True)

        # Eliminar los que exceden el límite
        archivos_a_eliminar = archivos[max_backups:]
        for archivo in archivos_a_eliminar:
            try:
                os.remove(archivo)
                eliminados += 1
                logger.debug(f"Backup antiguo eliminado: {archivo}")
            except OSError as e:
                logger.warning(f"No se pudo eliminar {archivo}: {e}")

        logger.info(
            f"Limpieza de backups completada: {eliminados} archivo(s) eliminado(s), "
            f"{min(len(archivos), max_backups)} conservado(s)."
        )

    except Exception as e:
        logger.error(f"Error durante la limpieza de backups: {e}")

    return eliminados


# ═══════════════════════════════════════════════════════════════════════════
# Verificación de credenciales
# ═══════════════════════════════════════════════════════════════════════════

def verificar_credenciales_drive() -> bool:
    """Verifica si existe el archivo de credenciales de Google Drive.

    Comprueba la presencia de ``google_credentials.json`` en el directorio
    ``database/`` del proyecto.

    Returns:
        bool: ``True`` si el archivo existe, ``False`` en caso contrario.
    """
    return os.path.exists(CREDENTIALS_PATH)
