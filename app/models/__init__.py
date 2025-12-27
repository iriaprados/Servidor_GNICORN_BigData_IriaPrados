# ---- Inicilación del módulo de modelos ----

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .producto import Producto

__all__ = ['db', 'User', 'Producto']