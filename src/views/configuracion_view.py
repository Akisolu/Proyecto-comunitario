"""
Vista de configuración del sistema SGI Salud.

Permite al usuario personalizar:
  • Tema de colores (oscuro, claro, personalizado con selectores visuales).
  • Tamaño de fuente (pequeño, normal, grande, muy grande) con vista previa.
  • Modo de número de historia (manual o automático).
  • Copias de seguridad (local automático, programado por horario, nube).

Los cambios se persisten en disco y se aplican en caliente al guardar
mediante el callback on_config_changed(new_config).

Cambios v3:
    - Sección de copias de seguridad con backup local y Google Drive.
"""

import re
import customtkinter as ctk

from models.config import AppConfig, cargar_config, guardar_config, ColoresPersonalizados
from models.tema import obtener_tema, obtener_tamano_fuente, TEMA_OSCURO, TEMA_CLARO, TAMANOS_FUENTE
from views.selector_color_widget import SelectorColorPopup
from utils.backup_service import (
    realizar_backup_local, subir_a_google_drive,
    verificar_credenciales_drive, limpiar_backups_antiguos,
)
from utils.hilo_trabajo import ejecutar_en_hilo


_PATRON_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


class ConfiguracionView(ctk.CTkFrame):
    """Vista de configuración general de la aplicación.

    Args:
        parent:            Widget padre.
        config:            Configuración actual (AppConfig).
        on_config_changed: Callback invocado tras guardar.
        tema:              Dict de colores del tema activo.
        fuentes:           Dict de tamaños de fuente activos.
    """

    _MAPA_TEMAS = {"Oscuro": "oscuro", "Claro": "claro", "Personalizado": "personalizado"}
    _MAPA_TEMAS_INV = {v: k for k, v in _MAPA_TEMAS.items()}
    _MAPA_TAMANOS = {"Pequeño": "pequeno", "Normal": "normal", "Grande": "grande", "Muy Grande": "muy_grande"}
    _MAPA_TAMANOS_INV = {v: k for k, v in _MAPA_TAMANOS.items()}
    _MAPA_MODO = {"Manual": "manual", "Automático": "auto"}
    _MAPA_MODO_INV = {v: k for k, v in _MAPA_MODO.items()}

    _CAMPOS_COLOR = [
        ("fondo",        "Fondo"),
        ("panel",        "Panel"),
        ("acento",       "Acento"),
        ("texto",        "Texto"),
        ("entrada_fondo", "Entrada"),
        ("fila_alterna", "Fila Alterna"),
    ]

    def __init__(self, parent, config, on_config_changed, tema=None, fuentes=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.config = config
        self.on_config_changed = on_config_changed

        # Colores dinámicos
        t = tema or obtener_tema(config)
        self.C_PANEL = t.get("panel", "#182633")
        self.C_ACENTO = t.get("acento", "#00A8E8")
        self.C_ACENTO_HOVER = t.get("acento_hover", "#007BB5")
        self.C_TEXTO = t.get("texto", "#E8EDF2")
        self.C_TEXTO_SEC = t.get("texto_secundario", "#8899AA")
        self.C_ENTRADA = t.get("entrada_fondo", "#1E3044")
        self.C_BORDE = t.get("entrada_borde", "#2A4158")
        self.C_EXITO = t.get("exito", "#00D68F")
        self.C_ERROR = t.get("error", "#FF4C6A")
        self._tema_dict = t  # Para pasar al color picker

        f = fuentes or obtener_tamano_fuente(config)
        self.F_BASE = f.get("base", 12)

        self._entradas_color: dict[str, ctk.CTkEntry] = {}
        self._previews_color: dict[str, ctk.CTkFrame] = {}
        self._crear_widgets()

    # ══════════════════════════════════════════════════════════════════
    #  INTERFAZ
    # ══════════════════════════════════════════════════════════════════

    def _crear_widgets(self):
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=self.C_ENTRADA,
            scrollbar_button_hover_color=self.C_ACENTO,
        )
        scroll.pack(fill="both", expand=True)
        self._scroll = scroll

        self._crear_encabezado(scroll)
        self._crear_seccion_tema(scroll)
        self._crear_seccion_fuente(scroll)
        self._crear_seccion_modo_historia(scroll)
        self._crear_seccion_paginacion(scroll)
        self._crear_seccion_backup(scroll)
        self._crear_boton_guardar(scroll)

    # ── Encabezado ────────────────────────────────────────────────────

    def _crear_encabezado(self, parent):
        card = ctk.CTkFrame(
            parent, fg_color=self.C_PANEL, corner_radius=12,
            border_width=1, border_color=self.C_BORDE,
        )
        card.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(
            card, text="⚙️ Configuración",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=self.C_TEXTO, anchor="w",
        ).pack(fill="x", padx=20, pady=(16, 2))
        ctk.CTkLabel(
            card, text="Personalice la apariencia y comportamiento. Los cambios se aplican de inmediato.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.C_TEXTO_SEC, anchor="w", wraplength=600,
        ).pack(fill="x", padx=20, pady=(0, 16))

    # ══════════════════════════════════════════════════════════════════
    #  SECCIÓN TEMA
    # ══════════════════════════════════════════════════════════════════

    def _crear_seccion_tema(self, parent):
        card = ctk.CTkFrame(
            parent, fg_color=self.C_PANEL, corner_radius=12,
            border_width=1, border_color=self.C_BORDE,
        )
        card.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            card, text="🎨 Tema de Colores",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=self.C_TEXTO, anchor="w",
        ).pack(fill="x", padx=20, pady=(16, 10))

        tema_label = self._MAPA_TEMAS_INV.get(self.config.tema, "Oscuro")
        self.selector_tema = ctk.CTkSegmentedButton(
            card, values=["Oscuro", "Claro", "Personalizado"],
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=self.C_ENTRADA,
            selected_color=self.C_ACENTO, selected_hover_color=self.C_ACENTO_HOVER,
            unselected_color=self.C_ENTRADA, unselected_hover_color=self.C_BORDE,
            text_color=self.C_TEXTO, command=self._al_cambiar_tema,
        )
        self.selector_tema.set(tema_label)
        self.selector_tema.pack(fill="x", padx=20, pady=(0, 12))

        # Panel de colores personalizados
        self.panel_colores = ctk.CTkFrame(
            card, fg_color=self.C_ENTRADA, corner_radius=10,
            border_width=1, border_color=self.C_BORDE,
        )
        if self.config.tema == "personalizado":
            self.panel_colores.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkLabel(
            self.panel_colores, text="Colores Personalizados",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=self.C_TEXTO, anchor="w",
        ).pack(fill="x", padx=14, pady=(10, 6))

        colores_actuales = self.config.colores_personalizados
        for campo, etiqueta in self._CAMPOS_COLOR:
            self._crear_fila_color(
                self.panel_colores, campo, etiqueta,
                getattr(colores_actuales, campo),
            )

        ctk.CTkFrame(card, fg_color="transparent", height=4).pack()

    def _crear_fila_color(self, parent, campo, etiqueta, valor_inicial):
        """Fila: [Etiqueta] [Entry hex] [Preview clicable]."""
        fila = ctk.CTkFrame(parent, fg_color="transparent")
        fila.pack(fill="x", padx=14, pady=2)

        ctk.CTkLabel(
            fila, text=etiqueta, width=85, anchor="w",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.C_TEXTO,
        ).pack(side="left", padx=(0, 6))

        entrada = ctk.CTkEntry(
            fila, font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=self.C_PANEL, border_color=self.C_BORDE,
            text_color=self.C_TEXTO, width=100, height=28, corner_radius=6,
        )
        entrada.insert(0, valor_inicial)
        entrada.pack(side="left", padx=(0, 6))
        entrada.bind("<KeyRelease>", lambda e, c=campo: self._actualizar_preview(c))
        self._entradas_color[campo] = entrada

        # Preview clicable — abre el SelectorColorPopup
        preview = ctk.CTkFrame(
            fila, fg_color=valor_inicial, width=28, height=28,
            corner_radius=6, border_width=1, border_color=self.C_BORDE,
        )
        preview.pack(side="left")
        preview.pack_propagate(False)
        preview.bind("<Button-1>", lambda e, c=campo: self._abrir_color_picker(c))
        self._previews_color[campo] = preview

    def _abrir_color_picker(self, campo):
        """Abre el selector visual de color para el campo dado."""
        color_actual = self._entradas_color[campo].get().strip()
        if not _PATRON_HEX.match(color_actual):
            color_actual = "#0F1923"

        widget_preview = self._previews_color[campo]
        SelectorColorPopup(
            widget_preview,
            callback=lambda hex_c, c=campo: self._al_seleccionar_color(c, hex_c),
            color_inicial=color_actual,
            colores_tema=self._tema_dict,
        )

    def _al_seleccionar_color(self, campo, hex_color):
        """Callback del color picker: actualiza entry y preview."""
        self._entradas_color[campo].delete(0, "end")
        self._entradas_color[campo].insert(0, hex_color)
        self._previews_color[campo].configure(
            fg_color=hex_color, border_color=self.C_BORDE,
        )
        self._entradas_color[campo].configure(border_color=self.C_BORDE)

    def _actualizar_preview(self, campo):
        """Actualiza el cuadro de preview al escribir un hex manualmente."""
        valor = self._entradas_color[campo].get().strip()
        if _PATRON_HEX.match(valor):
            self._previews_color[campo].configure(
                fg_color=valor, border_color=self.C_BORDE,
            )
            self._entradas_color[campo].configure(border_color=self.C_BORDE)
        else:
            self._previews_color[campo].configure(border_color=self.C_ERROR)
            self._entradas_color[campo].configure(border_color=self.C_ERROR)

    def _al_cambiar_tema(self, valor):
        if valor == "Personalizado":
            self.panel_colores.pack(fill="x", padx=20, pady=(0, 16))
        else:
            self.panel_colores.pack_forget()

    # ══════════════════════════════════════════════════════════════════
    #  SECCIÓN FUENTE
    # ══════════════════════════════════════════════════════════════════

    def _crear_seccion_fuente(self, parent):
        card = ctk.CTkFrame(
            parent, fg_color=self.C_PANEL, corner_radius=12,
            border_width=1, border_color=self.C_BORDE,
        )
        card.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            card, text="🔤 Tamaño de Fuente",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=self.C_TEXTO, anchor="w",
        ).pack(fill="x", padx=20, pady=(16, 10))

        tamano_label = self._MAPA_TAMANOS_INV.get(self.config.tamano_fuente, "Normal")
        self.selector_tamano = ctk.CTkSegmentedButton(
            card, values=["Pequeño", "Normal", "Grande", "Muy Grande"],
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=self.C_ENTRADA,
            selected_color=self.C_ACENTO, selected_hover_color=self.C_ACENTO_HOVER,
            unselected_color=self.C_ENTRADA, unselected_hover_color=self.C_BORDE,
            text_color=self.C_TEXTO, command=self._al_cambiar_fuente,
        )
        self.selector_tamano.set(tamano_label)
        self.selector_tamano.pack(fill="x", padx=20, pady=(0, 12))

        # Vista previa
        marco = ctk.CTkFrame(
            card, fg_color=self.C_ENTRADA, corner_radius=8,
            border_width=1, border_color=self.C_BORDE,
        )
        marco.pack(fill="x", padx=20, pady=(0, 16))
        self.label_preview_fuente = ctk.CTkLabel(
            marco,
            text="Vista previa — Texto de ejemplo para verificar el tamaño.",
            font=ctk.CTkFont(family="Segoe UI", size=self.F_BASE),
            text_color=self.C_TEXTO, anchor="w", wraplength=500,
        )
        self.label_preview_fuente.pack(fill="x", padx=14, pady=10)

    def _al_cambiar_fuente(self, valor):
        clave = self._MAPA_TAMANOS.get(valor, "normal")
        tamano = TAMANOS_FUENTE.get(clave, TAMANOS_FUENTE["normal"])
        self.label_preview_fuente.configure(
            font=ctk.CTkFont(family="Segoe UI", size=tamano["base"]),
        )

    # ══════════════════════════════════════════════════════════════════
    #  SECCIÓN MODO HISTORIA
    # ══════════════════════════════════════════════════════════════════

    def _crear_seccion_modo_historia(self, parent):
        card = ctk.CTkFrame(
            parent, fg_color=self.C_PANEL, corner_radius=12,
            border_width=1, border_color=self.C_BORDE,
        )
        card.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            card, text="📋 Modo de N. Historia",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=self.C_TEXTO, anchor="w",
        ).pack(fill="x", padx=20, pady=(16, 10))

        modo_label = self._MAPA_MODO_INV.get(self.config.modo_num_historia, "Manual")
        self.selector_modo = ctk.CTkSegmentedButton(
            card, values=["Manual", "Automático"],
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=self.C_ENTRADA,
            selected_color=self.C_ACENTO, selected_hover_color=self.C_ACENTO_HOVER,
            unselected_color=self.C_ENTRADA, unselected_hover_color=self.C_BORDE,
            text_color=self.C_TEXTO, command=self._al_cambiar_modo,
        )
        self.selector_modo.set(modo_label)
        self.selector_modo.pack(fill="x", padx=20, pady=(0, 12))

        _DESCS = {
            "manual": "Ingrese el número de historia manualmente",
            "auto": "El sistema generará el siguiente número secuencial",
        }
        marco = ctk.CTkFrame(
            card, fg_color=self.C_ENTRADA, corner_radius=8,
            border_width=1, border_color=self.C_BORDE,
        )
        marco.pack(fill="x", padx=20, pady=(0, 16))
        self.label_desc_modo = ctk.CTkLabel(
            marco, text=_DESCS.get(self.config.modo_num_historia, _DESCS["manual"]),
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.C_TEXTO_SEC, anchor="w", wraplength=500,
        )
        self.label_desc_modo.pack(fill="x", padx=14, pady=10)

    def _al_cambiar_modo(self, valor):
        descs = {
            "Manual": "Ingrese el número de historia manualmente",
            "Automático": "El sistema generará el siguiente número secuencial",
        }
        self.label_desc_modo.configure(text=descs.get(valor, ""))

    def _crear_seccion_paginacion(self, parent):
        card = ctk.CTkFrame(
            parent, fg_color=self.C_PANEL, corner_radius=12,
            border_width=1, border_color=self.C_BORDE,
        )
        card.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            card, text="📄 Registros por Página",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=self.C_TEXTO, anchor="w",
        ).pack(fill="x", padx=20, pady=(16, 10))

        limite_actual = str(self.config.registros_por_pagina)
        if limite_actual not in ["10", "20", "50", "100"]:
            limite_actual = "20"

        self.selector_paginacion = ctk.CTkSegmentedButton(
            card, values=["10", "20", "50", "100"],
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=self.C_ENTRADA,
            selected_color=self.C_ACENTO, selected_hover_color=self.C_ACENTO_HOVER,
            unselected_color=self.C_ENTRADA, unselected_hover_color=self.C_BORDE,
            text_color=self.C_TEXTO,
        )
        self.selector_paginacion.set(limite_actual)
        self.selector_paginacion.pack(fill="x", padx=20, pady=(0, 12))

        marco = ctk.CTkFrame(
            card, fg_color=self.C_ENTRADA, corner_radius=8,
            border_width=1, border_color=self.C_BORDE,
        )
        marco.pack(fill="x", padx=20, pady=(0, 16))
        ctk.CTkLabel(
            marco, text="Establece el número máximo de registros a mostrar por página en los listados.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.C_TEXTO_SEC, anchor="w", wraplength=500,
        ).pack(fill="x", padx=14, pady=10)

    # ══════════════════════════════════════════════════════════════════
    #  SECCIÓN COPIAS DE SEGURIDAD
    # ══════════════════════════════════════════════════════════════════

    def _crear_seccion_backup(self, parent):
        card = ctk.CTkFrame(
            parent, fg_color=self.C_PANEL, corner_radius=12,
            border_width=1, border_color=self.C_BORDE,
        )
        card.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            card, text="💾 Copias de Seguridad",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=self.C_TEXTO, anchor="w",
        ).pack(fill="x", padx=20, pady=(16, 10))

        # ── Backup Local ──
        marco_local = ctk.CTkFrame(card, fg_color=self.C_ENTRADA, corner_radius=8,
                                   border_width=1, border_color=self.C_BORDE)
        marco_local.pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(
            marco_local, text="Respaldo Local",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=self.C_TEXTO, anchor="w",
        ).pack(fill="x", padx=14, pady=(10, 4))

        # Checkbox: backup al cerrar
        self.chk_backup_cerrar = ctk.CTkCheckBox(
            marco_local, text="Crear copia automática al cerrar la aplicación",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.C_TEXTO, fg_color=self.C_ACENTO,
            hover_color=self.C_ACENTO_HOVER, border_color=self.C_BORDE,
            checkmark_color="#FFFFFF",
        )
        if self.config.backup_al_cerrar:
            self.chk_backup_cerrar.select()
        self.chk_backup_cerrar.pack(fill="x", padx=14, pady=2)

        # Checkbox: backup programado
        self.chk_backup_programado = ctk.CTkCheckBox(
            marco_local, text="Backup programado diario a las:",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.C_TEXTO, fg_color=self.C_ACENTO,
            hover_color=self.C_ACENTO_HOVER, border_color=self.C_BORDE,
            checkmark_color="#FFFFFF",
        )
        if self.config.backup_programado_habilitado:
            self.chk_backup_programado.select()
        self.chk_backup_programado.pack(fill="x", padx=14, pady=2)

        # Selector de hora
        fila_hora = ctk.CTkFrame(marco_local, fg_color="transparent")
        fila_hora.pack(fill="x", padx=14, pady=(2, 8))

        hora_actual = self.config.backup_programado_hora
        partes_hora = hora_actual.split(":")
        h_val = partes_hora[0] if len(partes_hora) == 2 else "23"
        m_val = partes_hora[1] if len(partes_hora) == 2 else "00"

        ctk.CTkLabel(
            fila_hora, text="Hora:",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.C_TEXTO_SEC,
        ).pack(side="left", padx=(20, 4))

        self.combo_hora = ctk.CTkComboBox(
            fila_hora, values=[f"{h:02d}" for h in range(24)],
            width=60, height=28,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=self.C_PANEL, border_color=self.C_BORDE,
            button_color=self.C_ACENTO, button_hover_color=self.C_ACENTO_HOVER,
            text_color=self.C_TEXTO, dropdown_fg_color=self.C_PANEL,
            dropdown_text_color=self.C_TEXTO, dropdown_hover_color=self.C_ACENTO,
        )
        self.combo_hora.set(h_val)
        self.combo_hora.pack(side="left", padx=(0, 4))

        ctk.CTkLabel(
            fila_hora, text=":",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=self.C_TEXTO,
        ).pack(side="left")

        self.combo_minuto = ctk.CTkComboBox(
            fila_hora, values=[f"{m:02d}" for m in range(0, 60, 5)],
            width=60, height=28,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=self.C_PANEL, border_color=self.C_BORDE,
            button_color=self.C_ACENTO, button_hover_color=self.C_ACENTO_HOVER,
            text_color=self.C_TEXTO, dropdown_fg_color=self.C_PANEL,
            dropdown_text_color=self.C_TEXTO, dropdown_hover_color=self.C_ACENTO,
        )
        self.combo_minuto.set(m_val)
        self.combo_minuto.pack(side="left", padx=(4, 0))

        # Botón de backup manual
        self.btn_backup_local = ctk.CTkButton(
            marco_local, text="📂 Crear Respaldo Local Ahora",
            height=32, corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=self.C_ACENTO, hover_color=self.C_ACENTO_HOVER,
            text_color="#FFFFFF", command=self._ejecutar_backup_local,
        )
        self.btn_backup_local.pack(fill="x", padx=14, pady=(0, 10))

        # ── Backup en la Nube (Google Drive) ──
        marco_nube = ctk.CTkFrame(card, fg_color=self.C_ENTRADA, corner_radius=8,
                                   border_width=1, border_color=self.C_BORDE)
        marco_nube.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkLabel(
            marco_nube, text="☁️ Respaldo en Google Drive",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=self.C_TEXTO, anchor="w",
        ).pack(fill="x", padx=14, pady=(10, 4))

        self.chk_backup_nube = ctk.CTkCheckBox(
            marco_nube, text="Habilitar respaldo en Google Drive",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.C_TEXTO, fg_color=self.C_ACENTO,
            hover_color=self.C_ACENTO_HOVER, border_color=self.C_BORDE,
            checkmark_color="#FFFFFF",
        )
        if self.config.backup_nube_habilitado:
            self.chk_backup_nube.select()
        self.chk_backup_nube.pack(fill="x", padx=14, pady=2)

        # Folder ID
        fila_folder = ctk.CTkFrame(marco_nube, fg_color="transparent")
        fila_folder.pack(fill="x", padx=14, pady=4)

        ctk.CTkLabel(
            fila_folder, text="ID Carpeta Drive:", width=120,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.C_TEXTO_SEC, anchor="w",
        ).pack(side="left")

        self.entrada_folder_id = ctk.CTkEntry(
            fila_folder,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=self.C_PANEL, border_color=self.C_BORDE,
            text_color=self.C_TEXTO, height=28, corner_radius=6,
            placeholder_text="Ej: 1ABC2def3GHI4jkl5MNO...",
        )
        self.entrada_folder_id.insert(0, self.config.backup_drive_folder_id)
        self.entrada_folder_id.pack(side="left", fill="x", expand=True)

        # Estado de credenciales
        tiene_creds = verificar_credenciales_drive()
        texto_creds = "✅ google_credentials.json detectado" if tiene_creds else "⚠️ Falta google_credentials.json en database/"
        color_creds = self.C_EXITO if tiene_creds else self.C_ERROR
        ctk.CTkLabel(
            marco_nube, text=texto_creds,
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=color_creds, anchor="w",
        ).pack(fill="x", padx=14, pady=(4, 4))

        # Botón de subir a Drive
        self.btn_backup_nube = ctk.CTkButton(
            marco_nube, text="☁️ Subir Respaldo a Google Drive Ahora",
            height=32, corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#4285F4", hover_color="#3367D6",
            text_color="#FFFFFF", command=self._ejecutar_backup_nube,
        )
        self.btn_backup_nube.pack(fill="x", padx=14, pady=(0, 10))

    def _ejecutar_backup_local(self):
        """Ejecuta un backup local manual en un hilo secundario."""
        self.btn_backup_local.configure(state="disabled", text="Creando respaldo...")

        def _on_resultado(resultado):
            exito, mensaje = resultado
            if exito:
                limpiar_backups_antiguos(10)
                self._mostrar_msg(f"✅ Respaldo local creado: {mensaje}", error=False)
            else:
                self._mostrar_msg(f"Error: {mensaje}", error=True)
            self.btn_backup_local.configure(state="normal", text="📂 Crear Respaldo Local Ahora")

        ejecutar_en_hilo(
            self,
            tarea=realizar_backup_local,
            callback_exito=_on_resultado,
            callback_error=lambda e: (
                self._mostrar_msg(f"Error: {e}", error=True),
                self.btn_backup_local.configure(state="normal", text="📂 Crear Respaldo Local Ahora"),
            ),
        )

    def _ejecutar_backup_nube(self):
        """Ejecuta un backup local y lo sube a Google Drive."""
        folder_id = self.entrada_folder_id.get().strip()
        if not folder_id:
            self._mostrar_msg("Ingrese el ID de la carpeta de Google Drive.", error=True)
            return
        if not verificar_credenciales_drive():
            self._mostrar_msg("Falta el archivo google_credentials.json en database/.", error=True)
            return

        self.btn_backup_nube.configure(state="disabled", text="Subiendo...")

        def _tarea():
            exito_local, ruta = realizar_backup_local()
            if not exito_local:
                return False, f"Error al crear backup local: {ruta}"
            return subir_a_google_drive(ruta, folder_id)

        def _on_resultado(resultado):
            exito, mensaje = resultado
            if exito:
                self._mostrar_msg(f"✅ Respaldo subido a Drive exitosamente.", error=False)
            else:
                self._mostrar_msg(f"Error Drive: {mensaje}", error=True)
            self.btn_backup_nube.configure(state="normal", text="☁️ Subir Respaldo a Google Drive Ahora")

        ejecutar_en_hilo(
            self,
            tarea=_tarea,
            callback_exito=_on_resultado,
            callback_error=lambda e: (
                self._mostrar_msg(f"Error: {e}", error=True),
                self.btn_backup_nube.configure(state="normal", text="☁️ Subir Respaldo a Google Drive Ahora"),
            ),
        )

    # ══════════════════════════════════════════════════════════════════
    #  GUARDAR
    # ══════════════════════════════════════════════════════════════════

    def _crear_boton_guardar(self, parent):
        marco = ctk.CTkFrame(parent, fg_color="transparent")
        marco.pack(fill="x", pady=(6, 16))

        ctk.CTkButton(
            marco, text="💾  Guardar Configuración",
            height=40, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=self.C_ACENTO, hover_color=self.C_ACENTO_HOVER,
            text_color="#FFFFFF", command=self._guardar,
        ).pack(fill="x", padx=20)

        self.label_mensaje = ctk.CTkLabel(
            marco, text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.C_EXITO, anchor="w",
        )
        self.label_mensaje.pack(fill="x", padx=24, pady=(6, 0))

    def _guardar(self):
        """Valida, persiste y notifica cambios de configuración."""
        try:
            tema_valor = self._MAPA_TEMAS.get(self.selector_tema.get(), "oscuro")
            tamano_valor = self._MAPA_TAMANOS.get(self.selector_tamano.get(), "normal")
            modo_valor = self._MAPA_MODO.get(self.selector_modo.get(), "manual")
            paginacion_valor = int(self.selector_paginacion.get())

            colores_pers = self.config.colores_personalizados
            if tema_valor == "personalizado":
                errores = self._validar_colores()
                if errores:
                    self._mostrar_msg(
                        f"Color inválido en: {', '.join(errores)}. Use formato #RRGGBB.",
                        error=True,
                    )
                    return
                colores_pers = self._recopilar_colores()

            # Recopilar configuración de backup
            hora_prog = f"{self.combo_hora.get()}:{self.combo_minuto.get()}"

            nueva = AppConfig(
                tema=tema_valor,
                tamano_fuente=tamano_valor,
                modo_num_historia=modo_valor,
                registros_por_pagina=paginacion_valor,
                colores_personalizados=colores_pers,
                backup_al_cerrar=bool(self.chk_backup_cerrar.get()),
                backup_programado_habilitado=bool(self.chk_backup_programado.get()),
                backup_programado_hora=hora_prog,
                backup_nube_habilitado=bool(self.chk_backup_nube.get()),
                backup_drive_folder_id=self.entrada_folder_id.get().strip(),
                backup_ultimo_dia_ejecutado=self.config.backup_ultimo_dia_ejecutado,
            )
            guardar_config(nueva)
            self._mostrar_msg("✅ Configuración guardada correctamente", error=False)

            if self.on_config_changed:
                self.on_config_changed(nueva)
        except Exception as e:
            self._mostrar_msg(f"Error al guardar: {e}", error=True)

    def _validar_colores(self):
        errores = []
        for campo, etiqueta in self._CAMPOS_COLOR:
            if not _PATRON_HEX.match(self._entradas_color[campo].get().strip()):
                errores.append(etiqueta)
        return errores

    def _recopilar_colores(self):
        datos = self.config.colores_personalizados.model_dump()
        for campo, _ in self._CAMPOS_COLOR:
            datos[campo] = self._entradas_color[campo].get().strip()
        return ColoresPersonalizados(**datos)

    def _mostrar_msg(self, texto, error=False):
        color = self.C_ERROR if error else self.C_EXITO
        self.label_mensaje.configure(text=texto, text_color=color)
        self.after(4000, lambda: self.label_mensaje.configure(text=""))
