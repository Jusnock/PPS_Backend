from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

# --- EMPRESAS ---
class CompanyCreate(BaseModel):
    nombre: str
    dominio_google: str

class CompanyResponse(BaseModel):
    id: int
    nombre: str
    dominio_google: str

    class Config:
        from_attributes = True

# --- USUARIOS ---
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    email: EmailStr
    nombre: str
    rol: Optional[str] = "EMPLEADO" # Roles: SUPERADMIN, ADMIN_EMPRESA, EMPLEADO
    company_id: Optional[int] = None
    password: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    nombre: str
    rol: str
    company_id: Optional[int] = None
    debe_cambiar_password: bool

    class Config:
        from_attributes = True

class PasswordChangeRequest(BaseModel):
    nueva_password: str

# --- ESCENARIOS (Preguntas / Correos HTML) ---
class ClueSchema(BaseModel):
    texto: str
    posicion: str # Recibe clases de Tailwind, ej: "top-14 left-10"

class ScenarioCreate(BaseModel):
    titulo_interno: str
    remitente_nombre: str
    remitente_email: str
    asunto_simulado: str
    cuerpo_html: str
    es_phishing: bool = True
    dificultad: str = "MEDIA"
    explicacion_titulo: Optional[str] = None
    explicacion_texto: Optional[str] = None
    clues: List[ClueSchema] = []
    
    # Si es Nulo, lo creó el SuperAdmin para todos. Si tiene ID, es exclusivo de un cliente.
    company_id: Optional[int] = None 

class ScenarioResponse(ScenarioCreate):
    id: int

    class Config:
        from_attributes = True

# --- QUIZZES (Campañas que agrupan escenarios) ---
class QuizCreate(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    activo: bool = True
    company_id: Optional[int] = None
    scenario_ids: List[int] = [] # El frontend enviará un arreglo con los IDs de las preguntas

class QuizResponse(BaseModel):
    id: int
    titulo: str
    descripcion: Optional[str]
    activo: bool
    fecha_creacion: datetime
    company_id: Optional[int]
    scenarios: List[ScenarioResponse] = [] # Devuelve los escenarios completos dentro del quiz

    class Config:
        from_attributes = True

# --- SESIONES Y ESTADÍSTICAS ---
class QuizSessionCreate(BaseModel):
    user_id: int
    quiz_id: int # Ahora la sesión sabe a qué campaña pertenece

class QuizSessionResponse(BaseModel):
    id: int
    user_id: int
    quiz_id: int
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None

    class Config:
        from_attributes = True

class SessionAnswerCreate(BaseModel):
    scenario_id: int
    identificado_como_phishing: bool
    tiempo_en_segundos: int

class SessionAnswerResponse(BaseModel):
    id: int
    session_id: int
    scenario_id: int
    identificado_como_phishing: bool
    acierto: bool
    tiempo_en_segundos: int

    class Config:
        from_attributes = True


class CompanyStatsResponse(BaseModel):
    total_empleados_registrados: int
    total_partidas_jugadas: int
    tasa_acierto_global_porcentaje: float
    tiempo_promedio_segundos: float