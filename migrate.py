# --------------- Migraciones de la base de datos ---------------
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) # Ruta raiz del proyecto, para que se puedan migrar los distintos modelos

from flask_migrate import Migrate, migrate, upgrade, downgrade, history, current
from app import create_app, db

app = create_app('development') # Crear app en modo desarrollo para migraciones
migrate_obj = Migrate(app, db) # Inicializar objeto Migrate

def main():

    with app.app_context(): # Contexto de la aplicación
        if len(sys.argv) < 2: # Verificar argumentos
            print("Uso: python migrate.py [migrate|upgrade|downgrade|history|current]")
            sys.exit(1)
        
        comando = sys.argv[1] # Obtener comando
        
        if comando == "migrate": # Crear migración
            mensaje = sys.argv[2] if len(sys.argv) > 2 else "Auto migration"
            print(f"Creando migracion: {mensaje}")
            migrate(message=mensaje)
            print("Migracion creada")
        
        elif comando == "upgrade": # Aplicar migraciones
            print("Aplicando migraciones...")
            upgrade()
            print("Migraciones aplicadas")
        
        elif comando == "downgrade": # Revertir migración
            print("Revirtiendo migracion...")
            downgrade()
            print("Migracion revertida")
        
        elif comando == "history": # Mostrar historial de migraciones
            print("Historial de migraciones:")
            history()
        
        elif comando == "current": # Mostrar versión actual
            print("Version actual:")
            current()
        
        else: # Comando desconocido
            print(f"Comando desconocido: {comando}")
            print("Comandos disponibles: migrate, upgrade, downgrade, history, current")

if __name__ == "__main__":
    main()