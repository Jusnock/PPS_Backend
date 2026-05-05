from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    SECRET_KEY: str
    SUPERADMIN_EMAILS: str = ""
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"
    DATABASE_URL: str = "postgresql://admin:Sistemas1.@localhost:5432/phishing_quiz"

    class Config:
        env_file = ".env"

settings = Settings()