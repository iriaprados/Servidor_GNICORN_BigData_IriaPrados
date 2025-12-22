
# ------- Archivo principal para ejecutar la aplicación Flask -------
import os
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Producto

# Crear la aplicación
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)

# Contexto de shell
@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Producto': Producto
    }

# Comando CLI personalizado
@app.cli.command()
def init_db():
    """Inicializa la base de datos"""
    db.create_all()
    print("✅ Base de datos inicializada")

# Comando para crear admin
@app.cli.command()
def create_admin():
    """Crea un usuario administrador"""
    username = input("Nombre de usuario admin: ")
    password = input("Contraseña: ")
    email = input("Email (opcional): ") or None
    
    if User.query.filter_by(username=username).first():
        print("❌ El usuario ya existe")
        return
    
    user = User(username=username, email=email, role='admin')
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    print(f"✅ Usuario admin '{username}' creado correctamente")

if __name__ == "__main__":
    print("=" * 60)
    print("INICIANDO SERVIDOR FLASK")
    print("=" * 60)
    
    # Auto-inicializar BD si no existe
    with app.app_context():
        try:
            # Verificar si las tablas existen
            db.create_all()
            
            user_count = User.query.count()
            print(f" Base de datos conectada ({user_count} usuarios)")
            
            if user_count == 0:
                print("\n  ADVERTENCIA: No hay usuarios en la base de datos")
                print("   Ejecuta en otra terminal: python admin.py")
            else:
                # Mostrar usuarios admin
                admins = User.query.filter_by(role='admin').all()
                if admins:
                    print(f" Usuarios admin: {', '.join([a.username for a in admins])}")
        
        except Exception as e:
            print(f"❌ Error al conectar con la base de datos: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print(" Servidor iniciando en: http://127.0.0.1:8000")
    print(" Swagger docs en: http://127.0.0.1:8000/apidocs/")
    print("=" * 60 + "\n")
    
    # Ejecutar aplicación
    app.run(
        debug=True,
        host="0.0.0.0",
        port=8000,
        use_reloader=True
    )
