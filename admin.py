# --- Definir el rol de admin y establecer su contraseña ---

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User

# Crear o actualizar el usuario administrador
def create_admin_user():

    app = create_app()
    
    with app.app_context():

        # Datos del admin
        username = "miusuario"
        password = "1234"
        email = "admin@ejemplo.com"
        
        # Buscar si existe
        user = User.query.filter_by(username=username).first()
        
        if user:
            # Actualizar existente
            user.set_password(password)
            user.role = 'admin'
            user.email = email
            db.session.commit()
            print(f" Usuario '{username}' actualizado como admin") # Actualizar existente

        else:
            # Crear nuevo
            user = User(username=username, email=email, role='admin')
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            print(f" Usuario '{username}' creado como admin") # Crear nuevo
        
        print(f"\nCredenciales:")
        print(f"   Usuario: {username}")
        print(f"   Contraseña: {password}")
        print(f"   Rol: admin")

if __name__ == "__main__":
    create_admin_user()
