from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, DateTime, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from sqlalchemy import Column, Boolean

# --- TABLAS INTERMEDIAS ---
# Tabla para relacionar Muchos-a-Muchos: Quizzes <-> Escenarios (Preguntas)
quiz_scenarios = Table(
    "quiz_scenarios",
    Base.metadata,
    Column("quiz_id", Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), primary_key=True),
    Column("scenario_id", Integer, ForeignKey("scenarios.id", ondelete="CASCADE"), primary_key=True)
)

# --- MODELOS PRINCIPALES ---

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    dominio_google = Column(String, unique=True, index=True) 
    
    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="company", cascade="all, delete-orphan")
    scenarios = relationship("Scenario", back_populates="company", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    nombre = Column(String)
    hashed_password = Column(String, nullable=True) 
    debe_cambiar_password = Column(Boolean, default=True)
    
    # Roles: SUPERADMIN, ADMIN_EMPRESA, EMPLEADO
    rol = Column(String, default="EMPLEADO") 
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    
    company = relationship("Company", back_populates="users")
    sessions = relationship("QuizSession", back_populates="user", cascade="all, delete-orphan")

class Scenario(Base):
    """Las 'Preguntas' sueltas o correos HTML"""
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True)
    titulo_interno = Column(String) # Para que el admin identifique la pregunta en su lista
    
    # --- Anatomía del Correo ---
    remitente_nombre = Column(String)
    remitente_email = Column(String)
    asunto_simulado = Column(String)
    cuerpo_html = Column(String)
    
    # --- Configuración del Motor ---
    es_phishing = Column(Boolean, default=True)
    dificultad = Column(String, default="MEDIA")
    
    # --- Retroalimentación (Jigsaw UI) ---
    explicacion_titulo = Column(String, nullable=True) # Ej: En realidad, este es un correo de phishing
    explicacion_texto = Column(String, nullable=True)  # Ej: El correo electrónico del remitente...
    clues = Column(JSON) # Guardará una lista: [{"texto": "...", "posicion": "top-14 left-10"}]
    
    # --- Relaciones ---
    # Si es Null, es global (SuperAdmin). Si tiene ID, es privado de una empresa.
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    company = relationship("Company", back_populates="scenarios")
    
    quizzes = relationship("Quiz", secondary=quiz_scenarios, back_populates="scenarios")

class Quiz(Base):
    """La 'Campaña' o evaluación que agrupa varios escenarios"""
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, index=True)
    descripcion = Column(String, nullable=True)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())

    # Si es Null, es global (SuperAdmin). Si tiene ID, es privado de una empresa.
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True)
    company = relationship("Company", back_populates="quizzes")
    
    scenarios = relationship("Scenario", secondary=quiz_scenarios, back_populates="quizzes")
    sessions = relationship("QuizSession", back_populates="quiz", cascade="all, delete-orphan")

class QuizSession(Base):
    """El intento de un empleado resolviendo un Quiz"""
    __tablename__ = "quiz_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"))
    fecha_inicio = Column(DateTime(timezone=True), server_default=func.now())
    fecha_fin = Column(DateTime(timezone=True), nullable=True)
    
    user = relationship("User", back_populates="sessions")
    quiz = relationship("Quiz", back_populates="sessions")
    answers = relationship("SessionAnswer", back_populates="session", cascade="all, delete-orphan")

class SessionAnswer(Base):
    """La respuesta exacta de un empleado a un escenario específico dentro de su sesión"""
    __tablename__ = "session_answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("quiz_sessions.id", ondelete="CASCADE"))
    scenario_id = Column(Integer, ForeignKey("scenarios.id", ondelete="CASCADE"))
    identificado_como_phishing = Column(Boolean)
    acierto = Column(Boolean)
    tiempo_en_segundos = Column(Integer)
    
    session = relationship("QuizSession", back_populates="answers")