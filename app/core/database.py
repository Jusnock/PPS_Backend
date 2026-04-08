from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Usamos las credenciales y el puerto que configuramos en el docker-compose.yml
SQLALCHEMY_DATABASE_URL = "postgresql://admin:Sistemas1.@localhost:5432/phishing_quiz"

# El engine es el motor principal que maneja la comunicación con Postgres
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# SessionLocal será la clase que instanciemos para cada request a la BD
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base es la clase de la que heredarán todos nuestros modelos ORM
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()