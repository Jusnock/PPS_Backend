from sqlalchemy.orm import Session
from app.models import models
from app.schemas import schemas
from app.core.security import get_password_hash
import random


# --- EMPRESAS (COMPANIES) ---
def get_company(db: Session, company_id: int):
    return db.query(models.Company).filter(models.Company.id == company_id).first()

def get_company_by_domain(db: Session, dominio: str):
    return db.query(models.Company).filter(models.Company.dominio_google == dominio).first()

def get_companies(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Company).offset(skip).limit(limit).all()

def create_company(db: Session, company: schemas.CompanyCreate):
    db_company = models.Company(
        nombre=company.nombre,
        dominio_google=company.dominio_google
    )
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company
def update_company(db: Session, company_id: int, company: schemas.CompanyCreate):
    db_company = get_company(db, company_id)
    if db_company:
        db_company.nombre = company.nombre
        db_company.dominio_google = company.dominio_google
        db.commit()
        db.refresh(db_company)
    return db_company

def delete_company(db: Session, company_id: int):
    db_company = get_company(db, company_id)
    if db_company:
        db.delete(db_company)
        db.commit()
    return db_company

# --- USUARIOS (USERS) ---
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    # Si viene con contraseña, la encriptamos. Si no, queda en None (Google SSO)
    hashed_pwd = get_password_hash(user.password) if user.password else None
    
    db_user = models.User(
        email=user.email,
        nombre=user.nombre,
        rol=user.rol,
        company_id=user.company_id,
        hashed_password=hashed_pwd
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: schemas.UserCreate):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db_user.nombre = user_update.nombre
        db_user.email = user_update.email
        
        # Si quien edita mandó un rol, lo actualizamos
        if user_update.rol:
            db_user.rol = user_update.rol
            
        # ¡LA MAGIA DEL RESETEO DE CONTRASEÑA!
        # Si el Admin escribió algo en el campo de contraseña...
        if user_update.password and len(user_update.password) > 0:
            # 1. Encriptamos la nueva contraseña temporal
            db_user.hashed_password = get_password_hash(user_update.password)
            # 2. Encendemos la alarma para que el empleado deba cambiarla apenas inicie sesión
            db_user.debe_cambiar_password = True 
            
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

# --- ESCENARIOS (SCENARIOS / PREGUNTAS) ---
def get_scenarios(db: Session, company_id: int = None):
    # Si manda company_id, trae los de la empresa + los globales (company_id = None)
    if company_id:
        return db.query(models.Scenario).filter(
            (models.Scenario.company_id == company_id) | (models.Scenario.company_id == None)
        ).all()
    # Si es SuperAdmin (company_id = None), trae solo los globales
    return db.query(models.Scenario).filter(models.Scenario.company_id == None).all()

def create_scenario(db: Session, scenario: schemas.ScenarioCreate):
    # Ya no usamos "remitente_simulado", usamos nombre y email separados, y agregamos pistas
    db_scenario = models.Scenario(
        titulo_interno=scenario.titulo_interno,
        remitente_nombre=scenario.remitente_nombre,
        remitente_email=scenario.remitente_email,
        asunto_simulado=scenario.asunto_simulado,
        cuerpo_html=scenario.cuerpo_html,
        es_phishing=scenario.es_phishing,
        dificultad=scenario.dificultad,
        explicacion_titulo=scenario.explicacion_titulo,
        explicacion_texto=scenario.explicacion_texto,
        # En Pydantic v2, para guardar listas de objetos como JSON, usamos model_dump()
        clues=[clue.model_dump() for clue in scenario.clues] if scenario.clues else [],
        company_id=scenario.company_id
    )
    db.add(db_scenario)
    db.commit()
    db.refresh(db_scenario)
    return db_scenario

def update_scenario(db: Session, scenario_id: int, scenario_update: schemas.ScenarioCreate):
    db_scenario = db.query(models.Scenario).filter(models.Scenario.id == scenario_id).first()
    if db_scenario:
        db_scenario.titulo_interno = scenario_update.titulo_interno
        db_scenario.remitente_nombre = scenario_update.remitente_nombre
        db_scenario.remitente_email = scenario_update.remitente_email
        db_scenario.asunto_simulado = scenario_update.asunto_simulado
        db_scenario.cuerpo_html = scenario_update.cuerpo_html
        db_scenario.es_phishing = scenario_update.es_phishing
        db_scenario.dificultad = scenario_update.dificultad
        db_scenario.explicacion_titulo = scenario_update.explicacion_titulo
        db_scenario.explicacion_texto = scenario_update.explicacion_texto
        db_scenario.clues = [clue.model_dump() for clue in scenario_update.clues] if scenario_update.clues else []
        
        db.commit()
        db.refresh(db_scenario)
    return db_scenario

def delete_scenario(db: Session, scenario_id: int):
    db_scenario = db.query(models.Scenario).filter(models.Scenario.id == scenario_id).first()
    if db_scenario:
        db.delete(db_scenario)
        db.commit()
    return db_scenario


# --- CAMPAÑAS (QUIZZES) ---
def get_quizzes(db: Session, company_id: int = None):
    # Trae las campañas de la empresa + las globales del SuperAdmin
    if company_id:
        return db.query(models.Quiz).filter(
            (models.Quiz.company_id == company_id) | (models.Quiz.company_id == None)
        ).all()
    return db.query(models.Quiz).filter(models.Quiz.company_id == None).all()

def create_quiz(db: Session, quiz: schemas.QuizCreate):
    # 1. Separamos los datos del Quiz
    quiz_data = quiz.dict(exclude={"scenario_ids"})
    db_quiz = models.Quiz(**quiz_data)
    
    # 2. SELECCIÓN ALEATORIA DE 10 PREGUNTAS (El "Jigsaw Engine")
    # Buscamos TODAS las preguntas que le pertenecen a esta empresa (o son globales)
    preguntas_disponibles = get_scenarios(db, company_id=quiz.company_id)
    
    # Mezclamos la lista de preguntas disponibles como una baraja de cartas
    random.shuffle(preguntas_disponibles)
    
    # Tomamos las primeras 10 (o menos, si el Admin aún no ha creado 10)
    preguntas_seleccionadas = preguntas_disponibles[:10]
    
    # Asignamos estas preguntas aleatorias a la campaña
    db_quiz.scenarios = preguntas_seleccionadas
        
    # 3. Guardamos en base de datos
    db.add(db_quiz)
    db.commit()
    db.refresh(db_quiz)
    
    return db_quiz

def update_quiz(db: Session, quiz_id: int, quiz_update: schemas.QuizCreate):
    db_quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
    if db_quiz:
        db_quiz.titulo = quiz_update.titulo
        db_quiz.descripcion = quiz_update.descripcion
        db_quiz.activo = quiz_update.activo
        # Actualizamos la relación de preguntas
        if quiz_update.scenario_ids is not None:
            escenarios = db.query(models.Scenario).filter(models.Scenario.id.in_(quiz_update.scenario_ids)).all()
            db_quiz.scenarios = escenarios
        db.commit()
        db.refresh(db_quiz)
    return db_quiz

def delete_quiz(db: Session, quiz_id: int):
    db_quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
    if db_quiz:
        db.delete(db_quiz)
        db.commit()
    return db_quiz
    
    # MAGIA RELACIONAL: Buscamos las preguntas por sus IDs y las metemos al Quiz
    if quiz.scenario_ids:
        escenarios = db.query(models.Scenario).filter(models.Scenario.id.in_(quiz.scenario_ids)).all()
        db_quiz.scenarios = escenarios

    db.add(db_quiz)
    db.commit()
    db.refresh(db_quiz)
    return db_quiz

# --- SESIONES Y RESPUESTAS (SESSIONS) ---
def create_quiz_session(db: Session, session: schemas.QuizSessionCreate, user_id: int):
    # Pasamos el user_id de forma explícita para evitar que Pydantic lo borre
    db_session = models.QuizSession(
        quiz_id=session.quiz_id,
        user_id=user_id
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def create_session_answer(db: Session, answer: schemas.SessionAnswerCreate, session_id: int, acierto: bool):
    db_answer = models.SessionAnswer(
        session_id=session_id,
        scenario_id=answer.scenario_id,
        identificado_como_phishing=answer.identificado_como_phishing,
        acierto=acierto,
        tiempo_en_segundos=answer.tiempo_en_segundos # <--- AGREGAMOS ESTO PARA GUARDARLO
    )
    db.add(db_answer)
    db.commit()
    db.refresh(db_answer)
    return db_answer


# ==========================================
#        REPORTES DE EMPLEADOS (NUEVO)
# ==========================================

def calcular_nivel_riesgo(tasa_acierto: float) -> str:
    if tasa_acierto >= 80:
        return "Protegido"
    elif tasa_acierto >= 50:
        return "Vulnerable"
    else:
        return "En Riesgo"

def get_user_report(db: Session, user_id: int):
    # Buscamos todas las sesiones del usuario
    sesiones = db.query(models.QuizSession).filter(models.QuizSession.user_id == user_id).all()
    session_ids = [s.id for s in sesiones]
    
    # Buscamos las respuestas de esas sesiones
    respuestas = db.query(models.SessionAnswer).filter(models.SessionAnswer.session_id.in_(session_ids)).all()
    
    if not respuestas:
        return {
            "total_respuestas": 0,
            "tasa_acierto": 0.0,
            "tiempo_promedio": 0.0,
            "estado": "Sin Datos"
        }
        
    total = len(respuestas)
    aciertos = sum(1 for r in respuestas if r.acierto)
    tasa_acierto = round((aciertos / total) * 100, 1)
    
    tiempo_total = sum(r.tiempo_en_segundos for r in respuestas if r.tiempo_en_segundos)
    tiempo_promedio = round(tiempo_total / total, 1) if total > 0 else 0.0
    
    return {
        "total_respuestas": total,
        "tasa_acierto": tasa_acierto,
        "tiempo_promedio": tiempo_promedio,
        "estado": calcular_nivel_riesgo(tasa_acierto)
    }

# ==========================================
#        ESTADÍSTICAS DEL DASHBOARD
# ==========================================

def get_superadmin_dashboard_stats(db: Session):
    empresas = db.query(models.Company).all()
    resultado = []
    
    for emp in empresas:
        usuarios = db.query(models.User.id).filter(
            models.User.company_id == emp.id,
            models.User.rol == 'EMPLEADO'
        ).all()
        user_ids = [u.id for u in usuarios]
        
        if not user_ids:
            resultado.append({
                "empresa_nombre": emp.nombre,
                "dominio": emp.dominio_google,
                "empleados": 0,
                "partidas": 0,
                "tasa_acierto": 0.0,
                "riesgo": 0.0
            })
            continue 
            
        sesiones = db.query(models.QuizSession.id).filter(models.QuizSession.user_id.in_(user_ids)).all()
        session_ids = [s.id for s in sesiones]
        
        if not session_ids:
            resultado.append({
                "empresa_nombre": emp.nombre,
                "dominio": emp.dominio_google,
                "empleados": len(user_ids),
                "partidas": 0,
                "tasa_acierto": 0.0,
                "riesgo": 0.0
            })
            continue

        respuestas = db.query(models.SessionAnswer).filter(models.SessionAnswer.session_id.in_(session_ids)).all()
        
        if not respuestas:
            acierto = 0.0
        else:
            aciertos = sum(1 for r in respuestas if r.acierto)
            acierto = round((aciertos / len(respuestas)) * 100, 1)
            
        resultado.append({
            "empresa_nombre": emp.nombre,
            "dominio": emp.dominio_google,
            "empleados": len(user_ids),
            "partidas": len(session_ids),
            "tasa_acierto": acierto,
            "riesgo": round(100 - acierto, 1) if len(session_ids) > 0 else 0.0
        })
        
    return resultado


def get_admin_dashboard_stats(db: Session, company_id: int):
    # 1. Estadísticas Generales
    usuarios = db.query(models.User).filter(
        models.User.company_id == company_id,
        models.User.rol == 'EMPLEADO'
    ).all()
    user_ids = [u.id for u in usuarios]
    
    quizzes = db.query(models.Quiz).filter(
        (models.Quiz.company_id == company_id) | (models.Quiz.company_id == None)
    ).all()
    
    campanas_stats = []
    for q in quizzes:
        if not user_ids:
            acierto_pct = 0.0
            session_ids = []
        else:
            sesiones = db.query(models.QuizSession.id).filter(
                models.QuizSession.quiz_id == q.id,
                models.QuizSession.user_id.in_(user_ids)
            ).all()
            session_ids = [s.id for s in sesiones]
            
        if not session_ids:
            respuestas = []
        else:
            respuestas = db.query(models.SessionAnswer).filter(models.SessionAnswer.session_id.in_(session_ids)).all()
        
        if respuestas:
            aciertos = sum(1 for r in respuestas if r.acierto)
            acierto_pct = round((aciertos / len(respuestas)) * 100, 1)
        else:
            acierto_pct = 0.0
            
        campanas_stats.append({
            "campana": q.titulo,
            "partidas": len(session_ids),
            "tasa_acierto": acierto_pct,
            "riesgo": round(100 - acierto_pct, 1) if len(session_ids) > 0 else 0.0
        })

    # 2. Reporte Detallado por Empleado
    reporte_empleados = []
    for u in usuarios:
        # AHORA SÍ CONOCE ESTA FUNCIÓN PORQUE ESTÁ DECLARADA ARRIBA
        stats = get_user_report(db, u.id)
        if stats["total_respuestas"] > 0: 
            reporte_empleados.append({
                "id": u.id,
                "nombre": u.nombre,
                "email": u.email,
                "aciertos": stats["tasa_acierto"],
                "tiempo": stats["tiempo_promedio"],
                "estado": stats["estado"]
            })
            
    # Ordenamos a los empleados: los que están "En Riesgo" primero
    orden_riesgo = {"En Riesgo": 0, "Vulnerable": 1, "Protegido": 2}
    reporte_empleados.sort(key=lambda x: orden_riesgo.get(x["estado"], 3))

    return {
        "campanas": campanas_stats,
        "empleados": reporte_empleados
    }