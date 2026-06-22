import customtkinter as ctk
from controllers.auth_controller import AuthController
from views.recuperar_clave_view import RecuperarClaveView


class LoginView(ctk.CTkToplevel):
    """Ventana de inicio de sesión.
    Se comunica con AuthController para validar credenciales.
    Al autenticarse correctamente, destruye esta ventana y abre el Dashboard.
    """

    # ── Paleta de colores ──────────────────────────────────────────
    COLOR_BG_DARK = "#0F1923"
    COLOR_PANEL = "#182633"
    COLOR_ACCENT = "#00A8E8"
    COLOR_ACCENT_HOVER = "#007BB5"
    COLOR_TEXT = "#E8EDF2"
    COLOR_TEXT_SEC = "#8899AA"
    COLOR_ENTRY_BG = "#1E3044"
    COLOR_ENTRY_BORDER = "#2A4158"
    COLOR_ERROR = "#FF4C6A"
    COLOR_SUCCESS = "#00D68F"

    def __init__(self, master, on_login_success: callable):
        """
        Args:
            master: Ventana raíz (CTk).
            on_login_success: Callback que recibe el Usuario autenticado
                              y se ejecuta al loguearse con éxito.
        """
        super().__init__(master)
        self.auth_controller = AuthController()
        self.on_login_success = on_login_success

        self._configurar_ventana()
        self._crear_widgets()

        # Interceptar cierre de ventana
        self.protocol("WM_DELETE_WINDOW", self._on_cerrar)

        # Foco en el campo de usuario al abrir
        self.after(100, lambda: self.entry_usuario.focus_set())

    # ── Configuración de ventana ──────────────────────────────────
    def _configurar_ventana(self):
        self.title("Iniciar Sesión — Hospital Dr. Armando Delgado Montero")
        self.configure(fg_color=self.COLOR_BG_DARK)
        self.resizable(False, False)

        # Tamaño y centrado
        ancho, alto = 480, 620
        pantalla_ancho = self.winfo_screenwidth()
        pantalla_alto = self.winfo_screenheight()
        x = (pantalla_ancho - ancho) // 2
        y = (pantalla_alto - alto) // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

        # Hacer modal
        self.grab_set()

    # ── Construcción de widgets ───────────────────────────────────
    def _crear_widgets(self):
        # ── Panel central (card) ──
        self.panel = ctk.CTkFrame(
            self,
            fg_color=self.COLOR_PANEL,
            corner_radius=16,
            border_width=1,
            border_color=self.COLOR_ENTRY_BORDER,
        )
        self.panel.place(relx=0.5, rely=0.5, anchor="center",
                         relwidth=0.85, relheight=0.90)

        # ── Icono / indicador visual ──
        icono_frame = ctk.CTkFrame(
            self.panel, fg_color=self.COLOR_ACCENT,
            corner_radius=40, width=72, height=72,
        )
        icono_frame.pack(pady=(32, 0))
        icono_frame.pack_propagate(False)

        icono_label = ctk.CTkLabel(
            icono_frame, text="🏥", font=ctk.CTkFont(size=32),
            text_color="#FFFFFF",
        )
        icono_label.place(relx=0.5, rely=0.5, anchor="center")

        # ── Título ──
        ctk.CTkLabel(
            self.panel,
            text="Sistema de Gestión",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=self.COLOR_TEXT,
        ).pack(pady=(18, 2))

        ctk.CTkLabel(
            self.panel,
            text="Hospital Dr. Armando Delgado Montero",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.COLOR_TEXT_SEC,
        ).pack(pady=(0, 28))

        # ── Separador visual ──
        ctk.CTkFrame(
            self.panel, fg_color=self.COLOR_ENTRY_BORDER, height=1,
        ).pack(fill="x", padx=32, pady=(0, 24))

        # ── Campo: Usuario ──
        ctk.CTkLabel(
            self.panel,
            text="Usuario",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=self.COLOR_TEXT_SEC,
            anchor="w",
        ).pack(fill="x", padx=36, pady=(0, 6))

        self.entry_usuario = ctk.CTkEntry(
            self.panel,
            placeholder_text="Ingrese su usuario",
            height=42,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            fg_color=self.COLOR_ENTRY_BG,
            border_color=self.COLOR_ENTRY_BORDER,
            text_color=self.COLOR_TEXT,
            placeholder_text_color=self.COLOR_TEXT_SEC,
        )
        self.entry_usuario.pack(fill="x", padx=36, pady=(0, 16))

        # ── Campo: Contraseña ──
        ctk.CTkLabel(
            self.panel,
            text="Contraseña",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=self.COLOR_TEXT_SEC,
            anchor="w",
        ).pack(fill="x", padx=36, pady=(0, 6))

        self.entry_clave = ctk.CTkEntry(
            self.panel,
            placeholder_text="Ingrese su contraseña",
            show="●",
            height=42,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            fg_color=self.COLOR_ENTRY_BG,
            border_color=self.COLOR_ENTRY_BORDER,
            text_color=self.COLOR_TEXT,
            placeholder_text_color=self.COLOR_TEXT_SEC,
        )
        self.entry_clave.pack(fill="x", padx=36, pady=(0, 8))

        # ── Label de mensajes (éxito / error) ──
        self.label_mensaje = ctk.CTkLabel(
            self.panel,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.COLOR_ERROR,
            wraplength=320,
        )
        self.label_mensaje.pack(fill="x", padx=36, pady=(4, 12))

        # ── Botón: Iniciar Sesión ──
        self.btn_login = ctk.CTkButton(
            self.panel,
            text="Iniciar Sesión",
            height=44,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            fg_color=self.COLOR_ACCENT,
            hover_color=self.COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            command=self._intentar_login,
        )
        self.btn_login.pack(fill="x", padx=36, pady=(0, 12))

        # ── Botón: Olvidé mi contraseña ──
        self.btn_recuperar = ctk.CTkButton(
            self.panel,
            text="¿Olvidó su contraseña?",
            height=30,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=12, underline=True),
            fg_color="transparent",
            hover_color=self.COLOR_ENTRY_BG,
            text_color=self.COLOR_ACCENT,
            command=self._abrir_recuperacion,
        )
        self.btn_recuperar.pack(fill="x", padx=36, pady=(0, 12))

        # ── Bind: Enter para hacer login ──
        self.entry_usuario.bind("<Return>", lambda e: self.entry_clave.focus_set())
        self.entry_clave.bind("<Return>", lambda e: self._intentar_login())

    # ── Lógica de login ───────────────────────────────────────────
    def _intentar_login(self):
        """Recoge los datos de los campos y los envía al AuthController."""
        usuario = self.entry_usuario.get()
        clave = self.entry_clave.get()

        # Deshabilitar botón mientras procesa
        self.btn_login.configure(state="disabled", text="Verificando...")

        exito, mensaje = self.auth_controller.login(usuario, clave)

        if exito:
            self.label_mensaje.configure(
                text=mensaje, text_color=self.COLOR_SUCCESS,
            )
            # Esperar un instante para que el usuario vea el mensaje de éxito
            self.after(800, lambda: self._login_exitoso())
        else:
            self.label_mensaje.configure(
                text=mensaje, text_color=self.COLOR_ERROR,
            )
            self.btn_login.configure(state="normal", text="Iniciar Sesión")
            # Efecto visual: sacudir el campo de contraseña
            self._efecto_shake(self.entry_clave)

    def _login_exitoso(self):
        """Ejecuta el callback de éxito y destruye la ventana de login."""
        usuario = self.auth_controller.obtener_usuario_actual()
        self.grab_release()
        self.destroy()
        self.on_login_success(usuario)

    # ── Efecto shake para error ───────────────────────────────────
    def _efecto_shake(self, widget, veces=4, distancia=8, velocidad=40):
        """Anima un widget sacudiéndolo horizontalmente para indicar error."""
        pos_original = widget.winfo_x()

        def paso(i):
            if i >= veces * 2:
                widget.place_configure(x=pos_original) if widget.place_info() else None
                return
            offset = distancia if i % 2 == 0 else -distancia
            # Usar pack no permite mover, así que aplicamos un pad temporal
            widget.pack_configure(padx=(36 + offset, 36 - offset))
            self.after(velocidad, lambda: paso(i + 1))

        paso(0)

    # ── Manejo de cierre ──────────────────────────────────────────
    def _on_cerrar(self):
        """Al cerrar la ventana de login, se cierra toda la aplicación."""
        self.grab_release()
        self.master.destroy()

    def _abrir_recuperacion(self):
        """Abre la ventana de recuperación de contraseña."""
        RecuperarClaveView(self)
