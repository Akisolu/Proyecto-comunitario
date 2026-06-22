"""
Vista de Gestión de Usuarios — SGI Salud.

Módulo CRUD para administrar los usuarios del sistema.
Incluye listado en tabla, formulario de creación/edición,
y sección de cambio de contraseña con verificación.

Componentes principales:
    - Barra de herramientas con botones Nuevo, Guardar, Eliminar, Limpiar
    - Tabla de usuarios registrados con filas clicables
    - Formulario lateral para datos del usuario
    - Sección de cambio de contraseña (solo visible en modo edición)

Relación con otros módulos:
    - Usa UsuarioController para CRUD y cambio de clave
"""

import customtkinter as ctk
from controllers.usuario_controller import UsuarioController
from utils.hilo_trabajo import ejecutar_en_hilo


class UsuariosView(ctk.CTkFrame):
    """Módulo de gestión de usuarios con CRUD completo.

    Permite listar, crear, actualizar, eliminar usuarios del sistema
    y cambiar contraseñas con verificación de la clave actual.

    Atributos:
        controlador:              Instancia de UsuarioController.
        id_usuario_seleccionado:  ID del usuario cargado en el form (None si nuevo).
        _widgets_filas_tabla:     Lista de frames de filas renderizadas.
    """

    # ══════════════════════════════════════════════════════════════════
    #  CONSTRUCTOR
    # ══════════════════════════════════════════════════════════════════

    def __init__(self, parent, tema=None, fuentes=None, **kwargs):
        """Inicializa la vista de usuarios.

        Args:
            parent:  Widget padre donde se coloca este frame.
            tema:    Dict de colores del tema activo.
            fuentes: Dict de tamaños de fuente activos.
        """
        super().__init__(parent, fg_color="transparent", **kwargs)

        # Colores dinámicos
        t = tema or {}
        self.COLOR_BG = t.get("fondo", "#0F1923")
        self.COLOR_PANEL = t.get("panel", "#182633")
        self.COLOR_ACCENT = t.get("acento", "#00A8E8")
        self.COLOR_ACCENT_HOVER = t.get("acento_hover", "#007BB5")
        self.COLOR_TEXT = t.get("texto", "#E8EDF2")
        self.COLOR_TEXT_SEC = t.get("texto_secundario", "#8899AA")
        self.COLOR_ENTRY_BG = t.get("entrada_fondo", "#1E3044")
        self.COLOR_ENTRY_BORDER = t.get("entrada_borde", "#2A4158")
        self.COLOR_ERROR = t.get("error", "#FF4C6A")
        self.COLOR_SUCCESS = t.get("exito", "#00D68F")
        self.COLOR_WARNING = "#FFB800"
        self.COLOR_DANGER = t.get("peligro", "#FF4C6A")
        self.COLOR_DANGER_HOVER = t.get("peligro_hover", "#D93A5A")
        self.COLOR_ROW_ALT = t.get("fila_alterna", "#1A2D3D")

        self.controlador = UsuarioController()
        self.id_usuario_seleccionado: int | None = None
        self._widgets_filas_tabla: list[ctk.CTkFrame] = []
        self._construir_interfaz()
        self._cargar_datos_tabla()

    # ══════════════════════════════════════════════════════════════════
    #  CONSTRUCCIÓN DE LA INTERFAZ
    # ══════════════════════════════════════════════════════════════════

    def _construir_interfaz(self):
        """Construye la barra de herramientas, la tabla y el formulario."""

        # ── Barra de herramientas ──
        self._construir_barra_herramientas()

        # ── Mensaje de retroalimentación ──
        self.etiqueta_mensaje = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.COLOR_SUCCESS, anchor="w",
        )
        self.etiqueta_mensaje.pack(fill="x", padx=4, pady=(0, 6))

        # ── Contenedor principal (tabla izquierda + formulario derecho) ──
        contenedor_principal = ctk.CTkFrame(self, fg_color="transparent")
        contenedor_principal.pack(fill="both", expand=True)
        contenedor_principal.grid_columnconfigure(0, weight=65)
        contenedor_principal.grid_columnconfigure(1, weight=35)
        contenedor_principal.grid_rowconfigure(0, weight=1)

        self._construir_tabla(contenedor_principal)
        self._construir_formulario(contenedor_principal)

    # ── BARRA DE HERRAMIENTAS ─────────────────────────────────────────

    def _construir_barra_herramientas(self):
        """Barra superior con botones de acción: Nuevo, Guardar, Eliminar, Limpiar."""
        barra = ctk.CTkFrame(
            self, fg_color=self.COLOR_PANEL,
            corner_radius=12, border_width=1,
            border_color=self.COLOR_ENTRY_BORDER,
        )
        barra.pack(fill="x", pady=(0, 10))

        contenedor_botones = ctk.CTkFrame(barra, fg_color="transparent")
        contenedor_botones.pack(fill="x", padx=12, pady=10)

        estilo_boton = {
            "height": 34, "corner_radius": 8,
            "font": ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        }

        ctk.CTkButton(
            contenedor_botones, text="Nuevo",
            fg_color=self.COLOR_ACCENT,
            hover_color=self.COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._nuevo_usuario, **estilo_boton,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            contenedor_botones, text="Guardar",
            fg_color=self.COLOR_SUCCESS, hover_color="#00B377",
            text_color="#FFFFFF",
            command=self._guardar_usuario, **estilo_boton,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            contenedor_botones, text="Eliminar",
            fg_color=self.COLOR_DANGER,
            hover_color=self.COLOR_DANGER_HOVER,
            text_color="#FFFFFF",
            command=self._eliminar_usuario, **estilo_boton,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            contenedor_botones, text="Limpiar",
            fg_color=self.COLOR_ENTRY_BG,
            hover_color=self.COLOR_ENTRY_BORDER,
            text_color=self.COLOR_TEXT,
            command=self._limpiar_formulario, **estilo_boton,
        ).pack(side="left")

    # ── TABLA ─────────────────────────────────────────────────────────

    def _construir_tabla(self, parent):
        """Construye el panel izquierdo con la tabla de usuarios.

        Args:
            parent: Widget contenedor principal.
        """
        panel_tabla = ctk.CTkFrame(
            parent, fg_color=self.COLOR_PANEL,
            corner_radius=12, border_width=1,
            border_color=self.COLOR_ENTRY_BORDER,
        )
        panel_tabla.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(
            panel_tabla, text="Usuarios Registrados",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=self.COLOR_TEXT, anchor="w",
        ).pack(fill="x", padx=16, pady=(12, 6))

        # Cabecera de la tabla
        self._construir_cabecera_tabla(panel_tabla)

        # Área scrollable para las filas de datos
        self.scroll_tabla = ctk.CTkScrollableFrame(
            panel_tabla, fg_color="transparent",
            scrollbar_button_color=self.COLOR_ENTRY_BG,
            scrollbar_button_hover_color=self.COLOR_ACCENT,
        )
        self.scroll_tabla.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        nombres_columnas = ["Cedula", "Nombre Completo", "Usuario"]
        pesos_columnas = [1, 2, 1]
        for indice, peso in enumerate(pesos_columnas):
            self.scroll_tabla.grid_columnconfigure(indice, weight=peso)

    def _construir_cabecera_tabla(self, parent):
        """Dibuja la fila de cabecera con los nombres de columna.

        Args:
            parent: Panel de la tabla.
        """
        cabecera = ctk.CTkFrame(
            parent, fg_color=self.COLOR_ENTRY_BG,
            height=36, corner_radius=0,
        )
        cabecera.pack(fill="x", padx=4, pady=(0, 0))
        cabecera.pack_propagate(False)

        nombres_columnas = ["Cedula", "Nombre Completo", "Usuario"]
        pesos_columnas = [1, 2, 1]

        for indice, (nombre, peso) in enumerate(
            zip(nombres_columnas, pesos_columnas)
        ):
            cabecera.grid_columnconfigure(indice, weight=peso)
            ctk.CTkLabel(
                cabecera, text=nombre,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=self.COLOR_TEXT, anchor="w",
            ).grid(row=0, column=indice, sticky="ew", padx=10, pady=6)

    # ── FORMULARIO ────────────────────────────────────────────────────

    def _construir_formulario(self, parent):
        """Construye el panel derecho con el formulario de usuario.

        Incluye campos para nombre, apellido, cédula, usuario y clave,
        más una sección de cambio de contraseña (solo visible al editar).

        Args:
            parent: Widget contenedor principal.
        """
        panel_formulario = ctk.CTkFrame(
            parent, fg_color=self.COLOR_PANEL,
            corner_radius=12, border_width=1,
            border_color=self.COLOR_ENTRY_BORDER,
        )
        panel_formulario.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(
            panel_formulario, text="Datos del Usuario",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=self.COLOR_TEXT, anchor="w",
        ).pack(fill="x", padx=16, pady=(16, 12))

        ctk.CTkFrame(
            panel_formulario, fg_color=self.COLOR_ENTRY_BORDER, height=1,
        ).pack(fill="x", padx=16, pady=(0, 12))

        # Área scrollable para todos los campos
        scroll_form = ctk.CTkScrollableFrame(
            panel_formulario, fg_color="transparent",
            scrollbar_button_color=self.COLOR_ENTRY_BG,
            scrollbar_button_hover_color=self.COLOR_ENTRY_BORDER,
        )
        scroll_form.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Estilos reutilizables
        estilo_entrada = {
            "height": 38, "corner_radius": 8,
            "font": ctk.CTkFont(family="Segoe UI", size=13),
            "fg_color": self.COLOR_ENTRY_BG,
            "border_color": self.COLOR_ENTRY_BORDER,
            "text_color": self.COLOR_TEXT,
            "placeholder_text_color": self.COLOR_TEXT_SEC,
        }
        estilo_etiqueta = {
            "font": ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            "text_color": self.COLOR_TEXT_SEC, "anchor": "w",
        }

        # ── Campos principales del usuario ──
        ctk.CTkLabel(
            scroll_form, text="Nombre", **estilo_etiqueta
        ).pack(fill="x", padx=8, pady=(0, 4))
        self.entrada_nombre = ctk.CTkEntry(
            scroll_form, placeholder_text="Nombre del usuario", **estilo_entrada
        )
        self.entrada_nombre.pack(fill="x", padx=8, pady=(0, 10))

        ctk.CTkLabel(
            scroll_form, text="Apellido", **estilo_etiqueta
        ).pack(fill="x", padx=8, pady=(0, 4))
        self.entrada_apellido = ctk.CTkEntry(
            scroll_form, placeholder_text="Apellido del usuario", **estilo_entrada
        )
        self.entrada_apellido.pack(fill="x", padx=8, pady=(0, 10))

        ctk.CTkLabel(
            scroll_form, text="Cedula", **estilo_etiqueta
        ).pack(fill="x", padx=8, pady=(0, 4))
        self.entrada_cedula = ctk.CTkEntry(
            scroll_form, placeholder_text="Cedula (solo numeros)", **estilo_entrada
        )
        self.entrada_cedula.pack(fill="x", padx=8, pady=(0, 10))

        ctk.CTkLabel(
            scroll_form, text="Usuario", **estilo_etiqueta
        ).pack(fill="x", padx=8, pady=(0, 4))
        self.entrada_usuario = ctk.CTkEntry(
            scroll_form, placeholder_text="Nombre de usuario", **estilo_entrada
        )
        self.entrada_usuario.pack(fill="x", padx=8, pady=(0, 10))

        ctk.CTkLabel(
            scroll_form, text="Clave (registro)", **estilo_etiqueta
        ).pack(fill="x", padx=8, pady=(0, 4))
        self.entrada_clave = ctk.CTkEntry(
            scroll_form, placeholder_text="Clave de acceso",
            show="*", **estilo_entrada,
        )
        self.entrada_clave.pack(fill="x", padx=8, pady=(0, 10))

        # ── Preguntas de seguridad ──
        ctk.CTkLabel(
            scroll_form, text="Pregunta de Seguridad 1", **estilo_etiqueta
        ).pack(fill="x", padx=8, pady=(0, 4))
        self.entrada_pregunta1 = ctk.CTkEntry(
            scroll_form, placeholder_text="Ej: ¿Cuál es el nombre de tu primera mascota?", **estilo_entrada
        )
        self.entrada_pregunta1.pack(fill="x", padx=8, pady=(0, 10))

        ctk.CTkLabel(
            scroll_form, text="Respuesta 1", **estilo_etiqueta
        ).pack(fill="x", padx=8, pady=(0, 4))
        self.entrada_respuesta1 = ctk.CTkEntry(
            scroll_form, placeholder_text="Tu respuesta", **estilo_entrada
        )
        self.entrada_respuesta1.pack(fill="x", padx=8, pady=(0, 10))

        ctk.CTkLabel(
            scroll_form, text="Pregunta de Seguridad 2", **estilo_etiqueta
        ).pack(fill="x", padx=8, pady=(0, 4))
        self.entrada_pregunta2 = ctk.CTkEntry(
            scroll_form, placeholder_text="Ej: ¿En qué ciudad naciste?", **estilo_entrada
        )
        self.entrada_pregunta2.pack(fill="x", padx=8, pady=(0, 10))

        ctk.CTkLabel(
            scroll_form, text="Respuesta 2", **estilo_etiqueta
        ).pack(fill="x", padx=8, pady=(0, 4))
        self.entrada_respuesta2 = ctk.CTkEntry(
            scroll_form, placeholder_text="Tu respuesta", **estilo_entrada
        )
        self.entrada_respuesta2.pack(fill="x", padx=8, pady=(0, 10))

        ctk.CTkLabel(
            scroll_form, text="Pregunta de Seguridad 3", **estilo_etiqueta
        ).pack(fill="x", padx=8, pady=(0, 4))
        self.entrada_pregunta3 = ctk.CTkEntry(
            scroll_form, placeholder_text="Ej: ¿Cuál es tu color favorito?", **estilo_entrada
        )
        self.entrada_pregunta3.pack(fill="x", padx=8, pady=(0, 10))

        ctk.CTkLabel(
            scroll_form, text="Respuesta 3", **estilo_etiqueta
        ).pack(fill="x", padx=8, pady=(0, 4))
        self.entrada_respuesta3 = ctk.CTkEntry(
            scroll_form, placeholder_text="Tu respuesta", **estilo_entrada
        )
        self.entrada_respuesta3.pack(fill="x", padx=8, pady=(0, 10))

        # ── Etiqueta de errores de validación ──
        self.etiqueta_errores_formulario = ctk.CTkLabel(
            scroll_form, text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.COLOR_ERROR, anchor="w", wraplength=280,
        )
        self.etiqueta_errores_formulario.pack(fill="x", padx=8, pady=(4, 4))

        # ══════════════════════════════════════════════════════════════
        #  SECCIÓN: CAMBIAR CONTRASEÑA
        #  Solo visible cuando se selecciona un usuario existente.
        # ══════════════════════════════════════════════════════════════
        self.seccion_cambio_clave = ctk.CTkFrame(
            scroll_form, fg_color="transparent"
        )
        # NO se empaqueta aquí — se muestra/oculta dinámicamente

        ctk.CTkFrame(
            self.seccion_cambio_clave,
            fg_color=self.COLOR_ENTRY_BORDER, height=1,
        ).pack(fill="x", padx=0, pady=(8, 12))

        ctk.CTkLabel(
            self.seccion_cambio_clave, text="CAMBIAR CONTRASEÑA",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            text_color=self.COLOR_ACCENT, anchor="w",
        ).pack(fill="x", padx=8, pady=(0, 8))

        ctk.CTkLabel(
            self.seccion_cambio_clave, text="Contraseña Actual",
            **estilo_etiqueta,
        ).pack(fill="x", padx=8, pady=(0, 4))
        self.entrada_clave_actual = ctk.CTkEntry(
            self.seccion_cambio_clave,
            placeholder_text="Ingrese la contraseña actual",
            show="*", **estilo_entrada,
        )
        self.entrada_clave_actual.pack(fill="x", padx=8, pady=(0, 10))

        ctk.CTkLabel(
            self.seccion_cambio_clave, text="Nueva Contraseña",
            **estilo_etiqueta,
        ).pack(fill="x", padx=8, pady=(0, 4))
        self.entrada_clave_nueva = ctk.CTkEntry(
            self.seccion_cambio_clave,
            placeholder_text="Minimo 4 caracteres",
            show="*", **estilo_entrada,
        )
        self.entrada_clave_nueva.pack(fill="x", padx=8, pady=(0, 10))

        ctk.CTkLabel(
            self.seccion_cambio_clave, text="Confirmar Nueva Contraseña",
            **estilo_etiqueta,
        ).pack(fill="x", padx=8, pady=(0, 4))
        self.entrada_clave_confirmacion = ctk.CTkEntry(
            self.seccion_cambio_clave,
            placeholder_text="Repita la nueva contraseña",
            show="*", **estilo_entrada,
        )
        self.entrada_clave_confirmacion.pack(fill="x", padx=8, pady=(0, 10))

        ctk.CTkButton(
            self.seccion_cambio_clave, text="🔒 Cambiar Contraseña",
            height=34, corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=self.COLOR_WARNING, hover_color="#E0A500",
            text_color="#1A1A2E", command=self._cambiar_clave,
        ).pack(fill="x", padx=8, pady=(0, 8))

        self.etiqueta_mensaje_clave = ctk.CTkLabel(
            self.seccion_cambio_clave, text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.COLOR_SUCCESS, anchor="w", wraplength=280,
        )
        self.etiqueta_mensaje_clave.pack(fill="x", padx=8, pady=(0, 4))

    # ══════════════════════════════════════════════════════════════════
    #  CARGA DE DATOS
    # ══════════════════════════════════════════════════════════════════

    def _cargar_datos_tabla(self):
        """Obtiene la lista de usuarios en un hilo secundario y renderiza la tabla."""
        ejecutar_en_hilo(
            self,
            tarea=self.controlador.listar_usuarios,
            callback_exito=self._renderizar_tabla,
            callback_error=lambda e: self._mostrar_mensaje(
                f"Error al cargar usuarios: {e}", es_error=True
            ),
        )

    def _renderizar_tabla(self, usuarios):
        """Limpia y redibuja las filas de la tabla con los usuarios dados.

        Args:
            usuarios: Lista de objetos Usuario a mostrar.
        """
        for widget_fila in self._widgets_filas_tabla:
            widget_fila.destroy()
        self._widgets_filas_tabla.clear()

        if not usuarios:
            marco_vacio = ctk.CTkFrame(self.scroll_tabla, fg_color="transparent")
            marco_vacio.grid(row=0, column=0, columnspan=3, pady=40, sticky="ew")
            ctk.CTkLabel(
                marco_vacio, text="No hay usuarios registrados.",
                font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color=self.COLOR_TEXT_SEC,
            ).pack()
            self._widgets_filas_tabla.append(marco_vacio)
            return

        pesos_columnas = [1, 2, 1]

        for indice, usuario in enumerate(usuarios):
            color_fila = self.COLOR_ROW_ALT if indice % 2 == 0 else "transparent"
            marco_fila = ctk.CTkFrame(
                self.scroll_tabla, fg_color=color_fila,
                height=36, corner_radius=0,
            )
            marco_fila.grid(row=indice, column=0, columnspan=3, sticky="ew")
            marco_fila.grid_propagate(False)

            for indice_col, peso in enumerate(pesos_columnas):
                marco_fila.grid_columnconfigure(indice_col, weight=peso)

            nombre_completo = f"{usuario.nombre} {usuario.apellido}"
            valores = [str(usuario.cedula), nombre_completo, usuario.usuario]

            for indice_col, valor in enumerate(valores):
                etiqueta = ctk.CTkLabel(
                    marco_fila, text=valor,
                    font=ctk.CTkFont(family="Segoe UI", size=12),
                    text_color=self.COLOR_TEXT, anchor="w",
                )
                etiqueta.grid(
                    row=0, column=indice_col, sticky="ew", padx=10, pady=6
                )
                etiqueta.bind(
                    "<Button-1>",
                    lambda _, u=usuario: self._seleccionar_usuario(u),
                )

            marco_fila.bind(
                "<Button-1>",
                lambda _, u=usuario: self._seleccionar_usuario(u),
            )
            self._widgets_filas_tabla.append(marco_fila)

    # ══════════════════════════════════════════════════════════════════
    #  SELECCIÓN DE USUARIO
    # ══════════════════════════════════════════════════════════════════

    def _seleccionar_usuario(self, usuario):
        """Carga los datos del usuario seleccionado en el formulario.

        Muestra la sección de cambio de contraseña (solo en modo edición).

        Args:
            usuario: Objeto Usuario seleccionado de la tabla.
        """
        self.id_usuario_seleccionado = usuario.id
        self.etiqueta_errores_formulario.configure(text="")

        self._establecer_texto_entrada(self.entrada_nombre, usuario.nombre)
        self._establecer_texto_entrada(self.entrada_apellido, usuario.apellido)
        self._establecer_texto_entrada(self.entrada_cedula, str(usuario.cedula))
        self._establecer_texto_entrada(self.entrada_usuario, usuario.usuario)
        self.entrada_clave.delete(0, "end")
        
        self._establecer_texto_entrada(self.entrada_pregunta1, usuario.pregunta1 or "")
        self._establecer_texto_entrada(self.entrada_respuesta1, usuario.respuesta1 or "")
        self._establecer_texto_entrada(self.entrada_pregunta2, usuario.pregunta2 or "")
        self._establecer_texto_entrada(self.entrada_respuesta2, usuario.respuesta2 or "")
        self._establecer_texto_entrada(self.entrada_pregunta3, usuario.pregunta3 or "")
        self._establecer_texto_entrada(self.entrada_respuesta3, usuario.respuesta3 or "")

        # Mostrar sección de cambio de contraseña
        self.seccion_cambio_clave.pack(fill="x")
        self.etiqueta_mensaje_clave.configure(text="")

    # ══════════════════════════════════════════════════════════════════
    #  ACCIONES CRUD
    # ══════════════════════════════════════════════════════════════════

    def _nuevo_usuario(self):
        """Prepara el formulario para registrar un nuevo usuario.

        Limpia todos los campos y oculta la sección de cambio de contraseña.
        """
        self.id_usuario_seleccionado = None
        self._limpiar_formulario()
        self._mostrar_mensaje(
            "Complete los campos para registrar un nuevo usuario.", es_error=False
        )
        self.entrada_nombre.focus_set()

    def _guardar_usuario(self):
        """Registra o actualiza un usuario según el estado del formulario.

        La operación de BD se ejecuta en un hilo secundario.
        """
        datos = self._obtener_datos_formulario()
        if datos is None:
            return

        id_sel = self.id_usuario_seleccionado

        def _operacion():
            if id_sel is None:
                return self.controlador.registrar_usuario(datos)
            else:
                return self.controlador.actualizar_usuario(id_sel, datos)

        def _on_guardado(resultado):
            exito, mensaje = resultado
            if exito:
                self._mostrar_mensaje(mensaje, es_error=False)
                self._limpiar_formulario()
                self.id_usuario_seleccionado = None
                self._cargar_datos_tabla()
            else:
                self._mostrar_mensaje(mensaje, es_error=True)

        ejecutar_en_hilo(
            self,
            tarea=_operacion,
            callback_exito=_on_guardado,
            callback_error=lambda e: self._mostrar_mensaje(f"Error: {e}", es_error=True),
        )

    def _eliminar_usuario(self):
        """Desactiva (borrado lógico) el usuario seleccionado en un hilo secundario."""
        if self.id_usuario_seleccionado is None:
            self._mostrar_mensaje(
                "Seleccione un usuario de la tabla para eliminar.", es_error=True
            )
            return

        id_sel = self.id_usuario_seleccionado

        def _on_eliminado(resultado):
            exito, mensaje = resultado
            if exito:
                self._mostrar_mensaje(mensaje, es_error=False)
                self._limpiar_formulario()
                self.id_usuario_seleccionado = None
                self._cargar_datos_tabla()
            else:
                self._mostrar_mensaje(mensaje, es_error=True)

        ejecutar_en_hilo(
            self,
            tarea=lambda: self.controlador.eliminar_usuario(id_sel),
            callback_exito=_on_eliminado,
            callback_error=lambda e: self._mostrar_mensaje(f"Error: {e}", es_error=True),
        )

    # ══════════════════════════════════════════════════════════════════
    #  CAMBIO DE CONTRASEÑA
    # ══════════════════════════════════════════════════════════════════

    def _cambiar_clave(self):
        """Cambia la contraseña del usuario seleccionado.

        Valida que se haya seleccionado un usuario, luego delega
        la verificación y cambio al controlador (que verifica la
        contraseña actual, longitud mínima, y coincidencia).
        """
        if self.id_usuario_seleccionado is None:
            self.etiqueta_mensaje_clave.configure(
                text="Seleccione un usuario primero.",
                text_color=self.COLOR_ERROR,
            )
            return

        clave_actual = self.entrada_clave_actual.get()
        clave_nueva = self.entrada_clave_nueva.get()
        clave_confirmacion = self.entrada_clave_confirmacion.get()

        exito, mensaje = self.controlador.cambiar_clave(
            self.id_usuario_seleccionado,
            clave_actual,
            clave_nueva,
            clave_confirmacion,
        )

        color = self.COLOR_SUCCESS if exito else self.COLOR_ERROR
        self.etiqueta_mensaje_clave.configure(text=mensaje, text_color=color)

        if exito:
            self.entrada_clave_actual.delete(0, "end")
            self.entrada_clave_nueva.delete(0, "end")
            self.entrada_clave_confirmacion.delete(0, "end")

    # ══════════════════════════════════════════════════════════════════
    #  UTILIDADES
    # ══════════════════════════════════════════════════════════════════

    def _obtener_datos_formulario(self) -> dict | None:
        """Lee los campos del formulario y valida que no estén vacíos.

        Verifica que todos los campos obligatorios tengan valor y que
        la cédula sea numérica.

        Returns:
            Diccionario con los datos del usuario o None si hay errores.
        """
        nombre = self.entrada_nombre.get().strip()
        apellido = self.entrada_apellido.get().strip()
        cedula_texto = self.entrada_cedula.get().strip()
        usuario = self.entrada_usuario.get().strip()
        clave = self.entrada_clave.get().strip()
        
        pregunta1 = self.entrada_pregunta1.get().strip()
        respuesta1 = self.entrada_respuesta1.get().strip()
        pregunta2 = self.entrada_pregunta2.get().strip()
        respuesta2 = self.entrada_respuesta2.get().strip()
        pregunta3 = self.entrada_pregunta3.get().strip()
        respuesta3 = self.entrada_respuesta3.get().strip()

        # Validar campos obligatorios
        campos_vacios = []
        if not nombre:
            campos_vacios.append("Nombre")
        if not apellido:
            campos_vacios.append("Apellido")
        if not cedula_texto:
            campos_vacios.append("Cedula")
        if not usuario:
            campos_vacios.append("Usuario")
        if not clave:
            campos_vacios.append("Clave")

        if campos_vacios:
            self.etiqueta_errores_formulario.configure(
                text=f"Campos requeridos: {', '.join(campos_vacios)}",
                text_color=self.COLOR_ERROR,
            )
            return None

        # Validar que la cédula sea numérica
        try:
            cedula = int(cedula_texto)
        except ValueError:
            self.etiqueta_errores_formulario.configure(
                text="La cedula debe contener solo numeros.",
                text_color=self.COLOR_ERROR,
            )
            return None

        self.etiqueta_errores_formulario.configure(text="")

        return {
            "nombre": nombre,
            "apellido": apellido,
            "cedula": cedula,
            "usuario": usuario,
            "clave": clave,
            "pregunta1": pregunta1,
            "respuesta1": respuesta1,
            "pregunta2": pregunta2,
            "respuesta2": respuesta2,
            "pregunta3": pregunta3,
            "respuesta3": respuesta3,
        }

    def _limpiar_formulario(self):
        """Resetea todos los campos del formulario y oculta cambio de clave.

        Limpia los entries principales, las entries de cambio de contraseña,
        y oculta la sección de cambio de clave.
        """
        self.entrada_nombre.delete(0, "end")
        self.entrada_apellido.delete(0, "end")
        self.entrada_cedula.delete(0, "end")
        self.entrada_usuario.delete(0, "end")
        self.entrada_clave.delete(0, "end")
        
        self.entrada_pregunta1.delete(0, "end")
        self.entrada_respuesta1.delete(0, "end")
        self.entrada_pregunta2.delete(0, "end")
        self.entrada_respuesta2.delete(0, "end")
        self.entrada_pregunta3.delete(0, "end")
        self.entrada_respuesta3.delete(0, "end")
        
        self.etiqueta_errores_formulario.configure(text="")

        # Limpiar y ocultar sección de cambio de contraseña
        self.entrada_clave_actual.delete(0, "end")
        self.entrada_clave_nueva.delete(0, "end")
        self.entrada_clave_confirmacion.delete(0, "end")
        self.etiqueta_mensaje_clave.configure(text="")
        self.seccion_cambio_clave.pack_forget()

    @staticmethod
    def _establecer_texto_entrada(entrada, valor: str):
        """Limpia un CTkEntry y establece un nuevo valor.

        Args:
            entrada: Widget CTkEntry a modificar.
            valor: Texto a colocar en el entry.
        """
        entrada.delete(0, "end")
        entrada.insert(0, valor)

    def _mostrar_mensaje(self, mensaje: str, es_error: bool = False):
        """Muestra un mensaje en la etiqueta de retroalimentación.

        Args:
            mensaje: Texto del mensaje.
            es_error: True para color rojo, False para color verde.
        """
        color = self.COLOR_ERROR if es_error else self.COLOR_SUCCESS
        self.etiqueta_mensaje.configure(text=mensaje, text_color=color)
