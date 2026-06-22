from pydantic import BaseModel

class UsuarioBase(BaseModel):
    nombre: str
    apellido: str
    cedula: int
    usuario: str
    estado: int = 1  # 1: Activo, 0: Inactivo
    pregunta1: str | None = None
    respuesta1: str | None = None
    pregunta2: str | None = None
    respuesta2: str | None = None
    pregunta3: str | None = None
    respuesta3: str | None = None

class UsuarioCreate(UsuarioBase):
    clave: str  # La contraseña solo se pide al crear/registrar

class Usuario(UsuarioBase):
    id: int

    class Config:
        from_attributes = True