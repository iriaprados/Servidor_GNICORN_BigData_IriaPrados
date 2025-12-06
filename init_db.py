# ------ Inicialización de la base de datos ------

import sys
import os

# Asegurarse de que estamos en el directorio correcto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Producto

def init_database():
    """Inicializa la base de datos y crea las tablas"""
    print(" Iniciando configuración de la base de datos...")
    
    app = create_app('development')
    
    with app.app_context():
        # Crear todas las tablas
        print(" Creando tablas en la base de datos...")
        db.create_all()
        print("✅ Tablas creadas correctamente:")
        print("   - users")
        print("   - productos")
        
        # Verificar si existe algún usuario
        user_count = User.query.count()
        print(f"\n Usuarios en la base de datos: {user_count}")
        
        if user_count == 0:
            print("\n  No hay usuarios en la base de datos")
            print("   Ejecuta: python admin.py para crear un administrador")
        
        print("\n✅ Base de datos lista para usar")
        print("\n Próximos pasos:")
        print("   1. python admin.py          (crear usuario admin)")
        print("   2. python run.py            (iniciar servidor)")

if __name__ == "__main__":
    init_database()