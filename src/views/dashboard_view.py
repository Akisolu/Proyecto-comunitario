"""
Vista principal del Dashboard — SGI Salud.

Panel principal con menú lateral de navegación y área de contenido.
Gestiona la aplicación de temas en caliente y la carga dinámica de módulos.

Cambios v3:
    - Cache de vistas: las vistas se crean una sola vez y se reutilizan
      al navegar. Solo se destruyen/recrean al guardar configuración.
    - Nuevo módulo Tarjetero de Ingresos.
"""

import customtkinter as ctk
from models.usuario import Usuario
from models.config import cargar_config, AppConfig
from models.tema import obtener_tema, obtener_tamano_fuente
from views.pacientes_view import PacientesView
from views.colores_view import ColoresView
from views.usuarios_view import UsuariosView
from views.tarjetero_view import TarjeteroView
from views.configuracion_view import ConfiguracionView


class DashboardView(ctk.CTkToplevel):
    """Panel principal del sistema (Dashboard).

    Contiene un menú lateral con navegación, área de contenido donde
    se cargan módulos, y sistema de temas dinámicos.

    Atributos:
        usuario:           Datos del usuario autenticado.
        config:            Configuración actual (AppConfig).
        colores:           Diccionario de colores del tema activo.
        fuentes:           Diccionario de tamaños de fuente activos.
        menu_seleccionado: Clave del módulo actualmente activo.
        botones_menu:      Mapa clave → CTkButton del sidebar.
    """

    MENU_ITEMS = [
        {"texto": "📊  Inicio",          "clave": "inicio"},
        {"texto": "👤  Pacientes",        "clave": "pacientes"},
        {"texto": "🏥  Tarjetero",        "clave": "tarjetero"},
        {"texto": "🎨  Colores",          "clave": "colores"},
        {"texto": "👥  Usuarios",         "clave": "usuarios"},
        {"texto": "⚙️  Configuración",    "clave": "configuracion"},
    ]

    # Mapa de vistas cacheables (clave → clase). Inicio y Configuración NO se cachean.
    _VISTA_CLASES = {
        "pacientes": PacientesView,
        "tarjetero": TarjeteroView,
        "colores": ColoresView,
        "usuarios": UsuariosView,
    }

    def __init__(self, master, usuario: Usuario, on_logout: callable):
        super().__init__(master)
        self.usuario = usuario
        self.on_logout = on_logout
        self.menu_seleccionado = "inicio"
        self.botones_menu: dict[str, ctk.CTkButton] = {}

        # Cache de vistas: se crean una sola vez y se reutilizan
        self._cache_vistas: dict[str, ctk.CTkFrame] = {}
        self._vista_activa: ctk.CTkFrame | None = None

        # Cargar config y derivar colores/fuentes
        self.config = cargar_config()
        self._cargar_colores_desde_config()

        self._configurar_ventana()
        self._crear_layout()
        self._mostrar_pagina_inicio()
        self.protocol("WM_DELETE_WINDOW", self._on_cerrar)

    # ══════════════════════════════════════════════════════════════════
    #  SISTEMA DE TEMAS
    # ══════════════════════════════════════════════════════════════════

    def _cargar_colores_desde_config(self):
        """Lee colores y fuentes de la config actual y los guarda como atributos.
        También actualiza la base de datos de opciones de Tkinter para mantener
        el contraste de selección (fuente blanca sobre acento de color).
        """
        self.colores = obtener_tema(self.config)
        self.fuentes = obtener_tamano_fuente(self.config)

        # Actualizar opciones de selección a nivel global de la aplicación
        self.master.option_add("*Entry.selectForeground", "white")
        self.master.option_add("*Entry.selectBackground", self.colores.get("acento", "#0078D4"))

    def aplicar_tema(self, nueva_config: AppConfig):
        """Aplica un nuevo tema en caliente a todo el dashboard.

        Invalida el cache de vistas para que se recreen con los nuevos
        colores/fuentes. Reconstruye el sidebar y recarga la vista activa.

        Args:
            nueva_config: Nueva configuración con el tema a aplicar.
        """
        self.config = nueva_config
        self._cargar_colores_desde_config()
        c = self.colores

        # Reconfigurar fondo principal
        self.configure(fg_color=c["fondo"])

        # ── Invalidar cache de vistas (se recrearán con nuevos colores) ──
        self._invalidar_cache()

        # ── Reconstruir sidebar completo ──
        self.sidebar.destroy()
        self.botones_menu.clear()
        self._crear_sidebar()
        self._actualizar_estilo_menu(self.menu_seleccionado)

        # ── Header y área de contenido ──
        self.header_contenido.configure(fg_color=c["header"])
        self.label_titulo_pagina.configure(text_color=c["texto"])
        self.area_contenido.configure(fg_color=c["fondo"])

        # ── Recargar la vista activa ──
        self._limpiar_contenido()
        clave = self.menu_seleccionado
        if clave in self._VISTA_CLASES:
            vista = self._obtener_o_crear_vista(clave)
            vista.pack(fill="both", expand=True)
            self._vista_activa = vista
        elif clave == "configuracion":
            self._mostrar_configuracion()
        else:
            self._mostrar_pagina_inicio()

    # ══════════════════════════════════════════════════════════════════
    #  CONFIGURACIÓN DE VENTANA
    # ══════════════════════════════════════════════════════════════════

    def _configurar_ventana(self):
        self.title("Sistema de Gestión — Hospital Dr. Armando Delgado Montero")
        self.configure(fg_color=self.colores["fondo"])
        ancho, alto = 1100, 700
        x = (self.winfo_screenwidth() - ancho) // 2
        y = (self.winfo_screenheight() - alto) // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")
        self.minsize(850, 520)

    # ══════════════════════════════════════════════════════════════════
    #  LAYOUT PRINCIPAL
    # ══════════════════════════════════════════════════════════════════

    def _crear_layout(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._crear_sidebar()
        self._crear_area_contenido()

    # ══════════════════════════════════════════════════════════════════
    #  SIDEBAR (responsive con scroll interno)
    # ══════════════════════════════════════════════════════════════════

    def _crear_sidebar(self):
        c = self.colores
        self._widgets_sidebar_dinamicos = []

        self.sidebar = ctk.CTkFrame(
            self, fg_color=c["sidebar"], corner_radius=0, width=230,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(1, weight=1)  # scroll area expande
        self.sidebar.grid_columnconfigure(0, weight=1)

        # ── Header (logo + nombre) ──
        header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=14, pady=(16, 0))

        icono = ctk.CTkFrame(
            header, fg_color=c["acento"], corner_radius=10, width=36, height=36,
        )
        icono.pack(side="left", padx=(0, 10))
        icono.pack_propagate(False)
        ctk.CTkLabel(
            icono, text="🏥", font=ctk.CTkFont(size=18), text_color="#FFFFFF",
        ).place(relx=0.5, rely=0.5, anchor="center")

        info = ctk.CTkFrame(header, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            info, text="SGI Salud",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=c["texto"], anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            info, text="Hospital DADM",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=c["texto_secundario"], anchor="w",
        ).pack(fill="x")

        # ── Zona central scrollable (menú + perfil + logout) ──
        scroll_sidebar = ctk.CTkScrollableFrame(
            self.sidebar, fg_color="transparent",
            scrollbar_button_color=c["entrada_fondo"],
            scrollbar_button_hover_color=c["acento"],
        )
        scroll_sidebar.grid(row=1, column=0, sticky="nsew", padx=0, pady=(6, 0))

        # Separador
        sep1 = ctk.CTkFrame(scroll_sidebar, fg_color=c["separador"], height=1)
        sep1.pack(fill="x", padx=14, pady=(4, 8))
        self._widgets_sidebar_dinamicos.append(sep1)

        # Label de sección
        ctk.CTkLabel(
            scroll_sidebar, text="MENÚ PRINCIPAL",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            text_color=c["texto_tenue"], anchor="w",
        ).pack(fill="x", padx=18, pady=(0, 6))

        # Botones del menú
        for item in self.MENU_ITEMS:
            btn = ctk.CTkButton(
                scroll_sidebar, text=item["texto"], height=36, corner_radius=8,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                fg_color="transparent", hover_color=c["boton_hover"],
                text_color=c["texto_secundario"], anchor="w",
                command=lambda k=item["clave"]: self._seleccionar_menu(k),
            )
            btn.pack(fill="x", padx=10, pady=1)
            self.botones_menu[item["clave"]] = btn

        self._actualizar_estilo_menu("inicio")

        # Spacer
        ctk.CTkFrame(scroll_sidebar, fg_color="transparent", height=20).pack()

        # Separador inferior
        sep2 = ctk.CTkFrame(scroll_sidebar, fg_color=c["separador"], height=1)
        sep2.pack(fill="x", padx=14, pady=(0, 8))
        self._widgets_sidebar_dinamicos.append(sep2)

        # ── Perfil del usuario ──
        perfil = ctk.CTkFrame(scroll_sidebar, fg_color="transparent")
        perfil.pack(fill="x", padx=14, pady=(0, 6))

        self.avatar_frame = ctk.CTkFrame(
            perfil, fg_color=c["acento"], corner_radius=18, width=32, height=32,
        )
        self.avatar_frame.pack(side="left", padx=(0, 8))
        self.avatar_frame.pack_propagate(False)
        iniciales = self.usuario.nombre[0].upper() + self.usuario.apellido[0].upper()
        ctk.CTkLabel(
            self.avatar_frame, text=iniciales,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#FFFFFF",
        ).place(relx=0.5, rely=0.5, anchor="center")

        user_info = ctk.CTkFrame(perfil, fg_color="transparent")
        user_info.pack(side="left", fill="x", expand=True)
        self.label_nombre_usuario = ctk.CTkLabel(
            user_info,
            text=f"{self.usuario.nombre} {self.usuario.apellido}",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=c["texto"], anchor="w",
        )
        self.label_nombre_usuario.pack(fill="x")
        self.label_username = ctk.CTkLabel(
            user_info, text=f"@{self.usuario.usuario}",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=c["texto_secundario"], anchor="w",
        )
        self.label_username.pack(fill="x")

        # Botón cerrar sesión
        self.btn_logout = ctk.CTkButton(
            scroll_sidebar, text="🚪  Cerrar Sesión", height=34, corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=c["peligro"], hover_color=c["peligro_hover"],
            text_color="#FFFFFF", command=self._cerrar_sesion,
        )
        self.btn_logout.pack(fill="x", padx=10, pady=(4, 12))

    # ══════════════════════════════════════════════════════════════════
    #  ÁREA DE CONTENIDO
    # ══════════════════════════════════════════════════════════════════

    def _crear_area_contenido(self):
        c = self.colores
        self.area_contenido = ctk.CTkFrame(
            self, fg_color=c["fondo"], corner_radius=0,
        )
        self.area_contenido.grid(row=0, column=1, sticky="nsew")

        self.header_contenido = ctk.CTkFrame(
            self.area_contenido, fg_color=c["header"], corner_radius=0, height=48,
        )
        self.header_contenido.pack(fill="x")
        self.header_contenido.pack_propagate(False)

        self.label_titulo_pagina = ctk.CTkLabel(
            self.header_contenido, text="Inicio",
            font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
            text_color=c["texto"], anchor="w",
        )
        self.label_titulo_pagina.pack(side="left", padx=20, pady=10)

        self.contenedor_pagina = ctk.CTkFrame(
            self.area_contenido, fg_color="transparent",
        )
        self.contenedor_pagina.pack(fill="both", expand=True, padx=16, pady=16)

    # ══════════════════════════════════════════════════════════════════
    #  NAVEGACIÓN Y CACHE DE VISTAS
    # ══════════════════════════════════════════════════════════════════

    def _seleccionar_menu(self, clave: str):
        """Navega a un módulo del menú.

        Las vistas cacheables (pacientes, tarjetero, colores, usuarios)
        se crean una sola vez y se reutilizan con pack/pack_forget.
        Inicio y Configuración se recrean cada vez (son ligeras o
        necesitan reflejar estado actual).
        """
        if clave == self.menu_seleccionado:
            return
        self.menu_seleccionado = clave
        self._actualizar_estilo_menu(clave)

        # Ocultar la vista activa actual (sin destruir)
        self._ocultar_vista_activa()

        # Limpiar contenido no-cacheado (inicio, config, placeholder)
        self._limpiar_contenido_no_cacheado()

        titulos = {
            "inicio": "Inicio", "pacientes": "Gestión de Pacientes",
            "tarjetero": "Tarjetero de Ingresos",
            "colores": "Referencia de Colores", "usuarios": "Gestión de Usuarios",
            "configuracion": "Configuración",
        }
        self.label_titulo_pagina.configure(text=titulos.get(clave, clave))

        # Mostrar vista cacheable o crear vista temporal
        if clave in self._VISTA_CLASES:
            vista = self._obtener_o_crear_vista(clave)
            vista.pack(fill="both", expand=True)
            self._vista_activa = vista
        elif clave == "configuracion":
            self._mostrar_configuracion()
        elif clave == "inicio":
            self._mostrar_pagina_inicio()
        else:
            self._mostrar_pagina_placeholder()

    def _obtener_o_crear_vista(self, clave: str) -> ctk.CTkFrame:
        """Retorna la vista cacheada o la crea si no existe."""
        if clave not in self._cache_vistas:
            clase = self._VISTA_CLASES[clave]
            if clave == "usuarios":
                self._cache_vistas[clave] = clase(
                    self.contenedor_pagina,
                    tema=self.colores,
                    fuentes=self.fuentes,
                    usuario_actual=self.usuario,
                )
            else:
                self._cache_vistas[clave] = clase(
                    self.contenedor_pagina,
                    tema=self.colores,
                    fuentes=self.fuentes,
                )
        return self._cache_vistas[clave]

    def _invalidar_cache(self):
        """Destruye todas las vistas cacheadas para forzar su recreación.

        Se invoca SOLO al guardar configuración (aplicar_tema).
        """
        for vista in self._cache_vistas.values():
            try:
                vista.destroy()
            except Exception:
                pass
        self._cache_vistas.clear()
        self._vista_activa = None

    def _ocultar_vista_activa(self):
        """Oculta la vista activa actual sin destruirla."""
        if self._vista_activa is not None:
            self._vista_activa.pack_forget()
            self._vista_activa = None

    def _limpiar_contenido_no_cacheado(self):
        """Destruye solo widgets no-cacheados del contenedor de página.

        Los widgets cacheados se ocultan (pack_forget), no se destruyen.
        Esto elimina vistas temporales como Inicio, Configuración, Placeholder.
        """
        cacheados = set(self._cache_vistas.values())
        for widget in self.contenedor_pagina.winfo_children():
            if widget not in cacheados:
                widget.destroy()

    def _mostrar_configuracion(self):
        """Crea y muestra la vista de configuración (no cacheada)."""
        vista = ConfiguracionView(
            self.contenedor_pagina,
            config=self.config,
            on_config_changed=self._on_config_changed,
            tema=self.colores,
            fuentes=self.fuentes,
        )
        vista.pack(fill="both", expand=True)

    def _on_config_changed(self, nueva_config: AppConfig):
        """Aplica el nuevo tema en caliente a toda la app."""
        self.aplicar_tema(nueva_config)

    def _actualizar_estilo_menu(self, clave_activa: str):
        c = self.colores
        for clave, btn in self.botones_menu.items():
            if clave == clave_activa:
                btn.configure(
                    fg_color=c["acento"], text_color="#FFFFFF",
                    hover_color=c["acento_hover"],
                )
            else:
                btn.configure(
                    fg_color="transparent", text_color=c["texto_secundario"],
                    hover_color=c["boton_hover"],
                )

    def _limpiar_contenido(self):
        """Limpia todo el contenido del contenedor (usado por aplicar_tema)."""
        for widget in self.contenedor_pagina.winfo_children():
            widget.destroy()
        self._vista_activa = None

    # ══════════════════════════════════════════════════════════════════
    #  PÁGINA DE INICIO
    # ══════════════════════════════════════════════════════════════════

    def _mostrar_pagina_inicio(self):
        c = self.colores

        # Bienvenida
        bienvenida = ctk.CTkFrame(
            self.contenedor_pagina, fg_color=c["panel"],
            corner_radius=12, border_width=1, border_color=c["entrada_borde"],
        )
        bienvenida.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            bienvenida,
            text=f"Bienvenido/a, {self.usuario.nombre} {self.usuario.apellido}",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=c["texto"], anchor="w",
        ).pack(fill="x", padx=20, pady=(16, 2))

        ctk.CTkLabel(
            bienvenida,
            text="Sistema de Gestión de Información Estadística y Registros de Salud",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=c["texto_secundario"], anchor="w",
        ).pack(fill="x", padx=20, pady=(0, 16))

        # Cards de resumen
        cards_frame = ctk.CTkFrame(self.contenedor_pagina, fg_color="transparent")
        cards_frame.pack(fill="x", pady=(0, 16))

        cards = [
            ("Pacientes", "👤", "Busqueda, registro y gestion"),
            ("Colores", "🎨", "Referencia de clasificacion"),
            ("Usuarios", "👥", "Administracion de accesos"),
        ]
        for i, (titulo, icono, desc) in enumerate(cards):
            cards_frame.grid_columnconfigure(i, weight=1)
            card = ctk.CTkFrame(
                cards_frame, fg_color=c["panel"], corner_radius=10,
                border_width=1, border_color=c["entrada_borde"], height=100,
            )
            card.grid(row=0, column=i, padx=4, sticky="nsew")
            card.pack_propagate(False)
            ctk.CTkLabel(
                card, text=icono, font=ctk.CTkFont(size=24),
            ).pack(padx=14, pady=(12, 2), anchor="w")
            ctk.CTkLabel(
                card, text=titulo,
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                text_color=c["texto"], anchor="w",
            ).pack(fill="x", padx=14)
            ctk.CTkLabel(
                card, text=desc,
                font=ctk.CTkFont(family="Segoe UI", size=10),
                text_color=c["texto_secundario"], anchor="w",
            ).pack(fill="x", padx=14)

        # Info
        info = ctk.CTkFrame(
            self.contenedor_pagina, fg_color=c["panel"], corner_radius=12,
            border_width=1, border_color=c["entrada_borde"],
        )
        info.pack(fill="x")
        ctk.CTkLabel(
            info, text="ℹ️  Acerca del sistema",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=c["texto"], anchor="w",
        ).pack(fill="x", padx=20, pady=(14, 2))
        ctk.CTkLabel(
            info, text="Utilice el menú lateral para navegar entre módulos.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=c["texto_secundario"], anchor="w",
        ).pack(fill="x", padx=20, pady=(0, 14))

    def _mostrar_pagina_placeholder(self):
        c = self.colores
        ph = ctk.CTkFrame(
            self.contenedor_pagina, fg_color=c["panel"],
            corner_radius=12, border_width=1, border_color=c["entrada_borde"],
        )
        ph.pack(fill="both", expand=True)
        ctk.CTkLabel(ph, text="🚧", font=ctk.CTkFont(size=48)).pack(pady=(60, 10))
        ctk.CTkLabel(
            ph, text="Módulo en Construcción",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=c["texto"],
        ).pack()

    # ══════════════════════════════════════════════════════════════════
    #  ACCIONES
    # ══════════════════════════════════════════════════════════════════

    def _cerrar_sesion(self):
        self.destroy()
        self.on_logout()

    def _on_cerrar(self):
        """Cierre de la aplicación con backup automático si está configurado."""
        if not self.config.backup_al_cerrar:
            self.master.destroy()
            return

        # Mostrar ventana de progreso
        self._popup_backup = ctk.CTkToplevel(self)
        self._popup_backup.title("Copia de seguridad")
        self._popup_backup.geometry("360x130")
        self._popup_backup.resizable(False, False)
        self._popup_backup.transient(self)
        self._popup_backup.grab_set()
        self._popup_backup.configure(fg_color=self.colores.get("fondo", "#0F1923"))
        self._popup_backup.protocol("WM_DELETE_WINDOW", lambda: None)

        # Centrar
        self._popup_backup.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 360) // 2
        y = self.winfo_y() + (self.winfo_height() - 130) // 2
        self._popup_backup.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            self._popup_backup, text="💾 Creando copia de seguridad...",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=self.colores.get("texto", "#E8EDF2"),
        ).pack(padx=20, pady=(20, 6))

        self._label_backup_estado = ctk.CTkLabel(
            self._popup_backup, text="Respaldo local en progreso...",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.colores.get("texto_secundario", "#8899AA"),
        )
        self._label_backup_estado.pack(padx=20, pady=(0, 10))

        barra = ctk.CTkProgressBar(
            self._popup_backup, mode="indeterminate",
            progress_color=self.colores.get("acento", "#00A8E8"),
            fg_color=self.colores.get("entrada_fondo", "#1E3044"),
        )
        barra.pack(fill="x", padx=30, pady=(0, 16))
        barra.start()

        import threading

        def _proceso_backup():
            from utils.backup_service import realizar_backup_local, subir_a_google_drive
            from loguru import logger

            try:
                exito, resultado = realizar_backup_local()
                if exito:
                    logger.info(f"Backup al cerrar creado: {resultado}")
                    ruta_backup = resultado

                    # Subir a la nube si está habilitado
                    if (self.config.backup_nube_habilitado
                            and self.config.backup_drive_folder_id):
                        try:
                            self._popup_backup.after(
                                0, lambda: self._label_backup_estado.configure(
                                    text="Subiendo respaldo a Google Drive..."))
                        except Exception:
                            pass
                        ok, msg = subir_a_google_drive(
                            ruta_backup, self.config.backup_drive_folder_id)
                        if ok:
                            logger.info(f"Backup subido a Drive: {msg}")
                        else:
                            logger.warning(f"Error al subir a Drive: {msg}")
                else:
                    logger.warning(f"Error en backup al cerrar: {resultado}")
            except Exception as e:
                logger.error(f"Error inesperado en backup al cerrar: {e}")
            finally:
                try:
                    self._popup_backup.after(0, self.master.destroy)
                except Exception:
                    pass

        threading.Thread(target=_proceso_backup, daemon=True).start()

