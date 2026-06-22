import customtkinter as ctk
from controllers.auth_controller import AuthController

class RecuperarClaveView(ctk.CTkToplevel):
    """Ventana de recuperación de contraseña."""

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
    COLOR_WARNING = "#FFB800"

    def __init__(self, master):
        super().__init__(master)
        self.auth_controller = AuthController()
        self.id_usuario = None
        self.preguntas = []
        
        self._configurar_ventana()
        self._crear_paso_1()

        self.grab_set()

    def _configurar_ventana(self):
        self.title("Recuperar Contraseña")
        self.configure(fg_color=self.COLOR_BG_DARK)
        self.resizable(False, False)
        
        ancho, alto = 500, 600
        pantalla_ancho = self.winfo_screenwidth()
        pantalla_alto = self.winfo_screenheight()
        x = (pantalla_ancho - ancho) // 2
        y = (pantalla_alto - alto) // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    def _limpiar_panel(self):
        if hasattr(self, "panel"):
            self.panel.destroy()
            
        self.panel = ctk.CTkFrame(
            self, fg_color=self.COLOR_PANEL, corner_radius=16,
            border_width=1, border_color=self.COLOR_ENTRY_BORDER
        )
        self.panel.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.85, relheight=0.88)

    # ── Paso 1: Ingresar Usuario ──
    def _crear_paso_1(self):
        self._limpiar_panel()
        
        ctk.CTkLabel(
            self.panel, text="Recuperación de Contraseña",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=self.COLOR_TEXT,
        ).pack(pady=(30, 10))

        ctk.CTkLabel(
            self.panel, text="Paso 1: Ingrese su nombre de usuario",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=self.COLOR_TEXT_SEC,
        ).pack(pady=(0, 30))

        self.entry_usuario = ctk.CTkEntry(
            self.panel, placeholder_text="Usuario", height=42, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            fg_color=self.COLOR_ENTRY_BG, border_color=self.COLOR_ENTRY_BORDER,
            text_color=self.COLOR_TEXT
        )
        self.entry_usuario.pack(fill="x", padx=36, pady=(0, 15))
        self.entry_usuario.bind("<Return>", lambda e: self._buscar_usuario())

        self.lbl_mensaje1 = ctk.CTkLabel(self.panel, text="", text_color=self.COLOR_ERROR, wraplength=350)
        self.lbl_mensaje1.pack(fill="x", padx=36, pady=(0, 15))

        btn_buscar = ctk.CTkButton(
            self.panel, text="Buscar Usuario", height=44, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            fg_color=self.COLOR_ACCENT, hover_color=self.COLOR_ACCENT_HOVER,
            command=self._buscar_usuario
        )
        btn_buscar.pack(fill="x", padx=36, pady=(0, 10))
        
        btn_cancelar = ctk.CTkButton(
            self.panel, text="Cancelar", height=44, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            fg_color=self.COLOR_ENTRY_BG, hover_color=self.COLOR_ENTRY_BORDER,
            command=self.destroy
        )
        btn_cancelar.pack(fill="x", padx=36, pady=(0, 10))

    def _buscar_usuario(self):
        usuario = self.entry_usuario.get()
        print(f"[DEBUG] Buscando usuario: {usuario}")
        exito, resultado, id_usuario = self.auth_controller.obtener_preguntas_seguridad(usuario)
        print(f"[DEBUG] Resultado obtener_preguntas: exito={exito}, resultado={resultado}")
        
        if exito:
            self.preguntas = resultado
            self.id_usuario = id_usuario
            print("[DEBUG] Pasando al Paso 2...")
            self._crear_paso_2()
        else:
            self.lbl_mensaje1.configure(text=resultado)

    # ── Paso 2: Preguntas de Seguridad ──
    def _crear_paso_2(self):
        self._limpiar_panel()
        
        ctk.CTkLabel(
            self.panel, text="Preguntas de Seguridad",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=self.COLOR_TEXT,
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            self.panel, text="Paso 2: Responda al menos 1 pregunta",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=self.COLOR_TEXT_SEC,
        ).pack(pady=(0, 20))

        # Scrollable frame para las preguntas
        scroll = ctk.CTkScrollableFrame(self.panel, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        self.entradas_respuestas = []
        
        for i, pregunta in enumerate(self.preguntas):
            ctk.CTkLabel(
                scroll, text=f"Pregunta {i+1}: {pregunta}",
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                text_color=self.COLOR_TEXT_SEC, anchor="w", wraplength=350, justify="left"
            ).pack(fill="x", padx=10, pady=(10, 4))
            
            entrada = ctk.CTkEntry(
                scroll, placeholder_text="Su respuesta", height=38, corner_radius=8,
                font=ctk.CTkFont(family="Segoe UI", size=13),
                fg_color=self.COLOR_ENTRY_BG, border_color=self.COLOR_ENTRY_BORDER,
                text_color=self.COLOR_TEXT
            )
            entrada.pack(fill="x", padx=10, pady=(0, 10))
            entrada.bind("<Return>", lambda e: self._verificar_respuestas())
            self.entradas_respuestas.append(entrada)

        self.lbl_mensaje2 = ctk.CTkLabel(self.panel, text="", text_color=self.COLOR_ERROR, wraplength=350)
        self.lbl_mensaje2.pack(fill="x", padx=36, pady=(5, 5))

        btn_verificar = ctk.CTkButton(
            self.panel, text="Verificar Respuestas", height=44, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            fg_color=self.COLOR_ACCENT, hover_color=self.COLOR_ACCENT_HOVER,
            command=self._verificar_respuestas
        )
        btn_verificar.pack(fill="x", padx=36, pady=(5, 15))

    def _verificar_respuestas(self):
        respuestas = [e.get() for e in self.entradas_respuestas]
        print(f"[DEBUG] Verificando respuestas: {respuestas}")
        
        # Check if at least one is answered and correct
        alguna_correcta = False
        alguna_respondida = False
        
        for i, resp in enumerate(respuestas):
            if resp.strip():
                alguna_respondida = True
                es_correcta = self.auth_controller.verificar_respuesta_seguridad(self.id_usuario, i, resp)
                print(f"[DEBUG] Respuesta {i} ('{resp}'): correcta={es_correcta}")
                if es_correcta:
                    alguna_correcta = True
                    break
        
        if not alguna_respondida:
            self.lbl_mensaje2.configure(text="Debe responder al menos 1 pregunta.", text_color=self.COLOR_ERROR)
            return
            
        if alguna_correcta:
            self._crear_paso_3()
        else:
            self.lbl_mensaje2.configure(text="Respuestas incorrectas. Intente nuevamente.", text_color=self.COLOR_ERROR)

    # ── Paso 3: Nueva Contraseña ──
    def _crear_paso_3(self):
        self._limpiar_panel()
        
        ctk.CTkLabel(
            self.panel, text="Nueva Contraseña",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=self.COLOR_TEXT,
        ).pack(pady=(30, 10))

        ctk.CTkLabel(
            self.panel, text="Paso 3: Cree una nueva contraseña",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=self.COLOR_SUCCESS,
        ).pack(pady=(0, 30))

        ctk.CTkLabel(
            self.panel, text="Nueva Contraseña",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=self.COLOR_TEXT_SEC, anchor="w",
        ).pack(fill="x", padx=36, pady=(0, 4))
        
        self.entry_nueva = ctk.CTkEntry(
            self.panel, placeholder_text="Mínimo 4 caracteres", height=42, corner_radius=10,
            show="*", font=ctk.CTkFont(family="Segoe UI", size=14),
            fg_color=self.COLOR_ENTRY_BG, border_color=self.COLOR_ENTRY_BORDER,
            text_color=self.COLOR_TEXT
        )
        self.entry_nueva.pack(fill="x", padx=36, pady=(0, 15))

        ctk.CTkLabel(
            self.panel, text="Confirmar Contraseña",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=self.COLOR_TEXT_SEC, anchor="w",
        ).pack(fill="x", padx=36, pady=(0, 4))

        self.entry_conf = ctk.CTkEntry(
            self.panel, placeholder_text="Repita la nueva contraseña", height=42, corner_radius=10,
            show="*", font=ctk.CTkFont(family="Segoe UI", size=14),
            fg_color=self.COLOR_ENTRY_BG, border_color=self.COLOR_ENTRY_BORDER,
            text_color=self.COLOR_TEXT
        )
        self.entry_conf.pack(fill="x", padx=36, pady=(0, 15))
        
        self.entry_nueva.bind("<Return>", lambda e: self.entry_conf.focus_set())
        self.entry_conf.bind("<Return>", lambda e: self._guardar_clave())

        self.lbl_mensaje3 = ctk.CTkLabel(self.panel, text="", text_color=self.COLOR_ERROR, wraplength=350)
        self.lbl_mensaje3.pack(fill="x", padx=36, pady=(0, 15))

        btn_guardar = ctk.CTkButton(
            self.panel, text="Guardar Contraseña", height=44, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            fg_color=self.COLOR_WARNING, hover_color="#E0A500", text_color="#1A1A2E",
            command=self._guardar_clave
        )
        btn_guardar.pack(fill="x", padx=36, pady=(0, 15))

    def _guardar_clave(self):
        nueva = self.entry_nueva.get()
        conf = self.entry_conf.get()
        
        exito, msj = self.auth_controller.recuperar_clave(self.id_usuario, nueva, conf)
        if exito:
            self.lbl_mensaje3.configure(text=msj, text_color=self.COLOR_SUCCESS)
            self.after(2000, self.destroy)
        else:
            self.lbl_mensaje3.configure(text=msj, text_color=self.COLOR_ERROR)
