# ------ Inicialización de la aplicación Flask con arquitectura MVC ------

from flask import Flask, jsonify
from flask_migrate import Migrate
from flasgger import Swagger
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import redis

from app.cache import CacheManager
from app.config import config
from app.models import db

# Inicializar extensiones globalmente (sin vincular a app todavía)
migrate = Migrate(compare_type=True)
csrf = CSRFProtect()
swagger = Swagger()
redis_client = None

# Directorio base de la aplicación
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Fábrica de aplicación Flask
def create_app(config_name='default'):
    
    # Crear instancia de Flask con rutas a views/
    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, 'views', 'templates'),  # ← CAMBIO
        static_folder=os.path.join(BASE_DIR, 'views', 'static')        # ← CAMBIO
    )
    
    # Cargar configuración según entorno
    app.config.from_object(config[config_name])
    
    # Mostrar configuración clave en consola
    # Vistas de la aplicación
    print(f" Templates: {app.template_folder}")  
    print(f" Static: {app.static_folder}") 
    # Cache y base de datos        
    print(f" DATABASE_URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    print(f" REDIS_URL: {app.config.get('REDIS_URL')}")
    
    # Inicializar extensiones con la app
    initialize_extensions(app)
    
    # Configurar Swagger para documentación API
    configure_swagger(app)
    
    # Configurar ProxyFix para NGINX
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    print("🔧 ProxyFix configurado para NGINX")
    
    # Registrar todos los blueprints (MVC)
    register_blueprints(app)
    
    # Registrar manejadores de errores
    register_error_handlers(app)
    
    print("\n" + "="*60)
    print("APLICACIÓN FLASK INICIALIZADA (Arquitectura MVC)")
    print("="*60 + "\n")
    
    return app

# Inicializar extensiones Flask
def initialize_extensions(app):
 
    # Base de datos
    db.init_app(app)
    migrate.init_app(app, db)
    print("SQLAlchemy y Flask-Migrate inicializados")
    
    # CSRF Protection
    csrf.init_app(app)
    print("CSRF Protection activado")
    
    # Redis para caché
    global redis_client
    try:
        redis_client = redis.from_url(
            app.config['REDIS_URL'], 
            decode_responses=True
        )
        redis_client.ping()
        print("Redis conectado correctamente")
        
        # Inicializar gestor de caché
        cache_manager = CacheManager(redis_client)
        app.cache_manager = cache_manager
        print("CacheManager inicializado")
        
    except Exception as e:
        print(f" Redis no disponible: {e}")
        print("   La aplicación funcionará sin caché")
        redis_client = None
        app.cache_manager = None

# Configurar Swagger para documentación automática de la API REST
def configure_swagger(app):
 
    # Plantilla básica de Swagger
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "API REST - Arquitectura MVC",
            "description": "API con JWT, SQLAlchemy y patrón MVC",
            "version": "3.0.0",
            "contact": {
                "name": "Desarrollo de Servidor y Big Data",
                "url": "https://www.ucjc.edu"
            }
        },

        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header. Formato: 'Bearer {token}'"
            }
        },

        "security": [{"Bearer": []}]
    }
    
    Swagger(app, template=swagger_template)
    print("Swagger configurado en /apidocs")


# Registrar blueprints siguiendo arquitectura MVC
def register_blueprints(app):
    
    
    print("\n🔌 Registrando Blueprints (Arquitectura MVC):")
    print("-" * 60)
    
    #  BLUEPRINTS HTML (Vistas Web) 
    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.main import bp as main_bp
    
    app.register_blueprint(auth_bp)
    print("Blueprint 'auth' registrado (login, register, logout)")
    
    app.register_blueprint(main_bp)
    print("Blueprint 'main' registrado (index, seguro, inseguro)")
    
    #  BLUEPRINTS API REST  
    from app.blueprints.usuarios import bp as usuarios_bp
    from app.blueprints.productos import bp as productos_bp
    
    # Exentar APIs de CSRF (usan JWT en su lugar)
    csrf.exempt(usuarios_bp)
    csrf.exempt(productos_bp)
    
    app.register_blueprint(usuarios_bp, url_prefix='/api')
    print("Blueprint API 'usuarios' registrado en /api")
    
    app.register_blueprint(productos_bp, url_prefix='/api')
    print("Blueprint API 'productos' registrado en /api")
    
    print("-" * 60)
    print("Todos los Blueprints registrados correctamente\n")


# Registrar manejadores de errores personalizados
def register_error_handlers(app):
  
    
    @app.errorhandler(400)
    def error_400(error):
        """Bad Request"""
        return jsonify({
            'error': 'Solicitud incorrecta',
            'message': str(error)
        }), 400
    
    @app.errorhandler(401)
    def error_401(error):
        """Unauthorized"""
        return jsonify({
            'error': 'No autenticado',
            'message': 'Se requiere autenticación válida'
        }), 401
    
    @app.errorhandler(403)
    def error_403(error):
        """Forbidden"""
        return jsonify({
            'error': 'Acceso denegado',
            'message': 'No tienes permisos para acceder a este recurso'
        }), 403
    
    @app.errorhandler(404)
    def error_404(error):
        """Not Found"""
        return jsonify({
            'error': 'Recurso no encontrado',
            'message': 'La ruta solicitada no existe'
        }), 404
    
    @app.errorhandler(500)
    def error_500(error):
        """Internal Server Error"""
        return jsonify({
            'error': 'Error interno del servidor',
            'message': 'Ha ocurrido un error inesperado'
        }), 500
    
    print("Manejadores de errores registrados (400, 401, 403, 404, 500)")