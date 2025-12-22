# ------ Configuración de la aplicación ------

import os  
from datetime import timedelta

# Configuración base
class Config: 
    
    # Seguridad
    SECRET_KEY = os.environ.get("FLASK_SECRET", "claveSecretaLocal")
    JWT_SECRET = os.environ.get("JWT_SECRET", "jwt_secret_key_local")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 1

    # Base de datos ← ESTAS LÍNEAS DEBEN ESTAR INDENTADAS
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "SQLALCHEMY_DATABASE_URI", 
        "sqlite:///users.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False   

    # Redis
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # Sesiones
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Producción
    IS_PRODUCTION = os.environ.get("FLASK_ENV") == "production"
    SESSION_COOKIE_SECURE = IS_PRODUCTION


class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    TESTING = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}