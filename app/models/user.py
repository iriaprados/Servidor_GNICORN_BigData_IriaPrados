# -------------------------------- Modelo de Usuario ----------------------------
from . import db
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

# Tabla para los usuarios
class User(db.Model):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(50), default='user')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relación con productos
    productos = db.relationship('Producto', backref='owner', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password): # Contraseña segura
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password): # Verificar la contraseña
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self): # Convertir los datos del usuario a un diccionario
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }