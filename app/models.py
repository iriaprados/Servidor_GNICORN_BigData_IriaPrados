# ------- Modelos de la base de datos -------

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Tabla para los usuarios
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(50), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    productos = db.relationship('Producto', backref='owner', lazy=True, cascade='all, delete-orphan') # Relacionar con la tabla de los productos 

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

# Tabla para los productos
class Producto(db.Model):

    __tablename__ = 'productos' # Nombre de la tabla
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self): # Convertir los datos del producto a un diccionario
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'precio': self.precio,
            'stock': self.stock,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }