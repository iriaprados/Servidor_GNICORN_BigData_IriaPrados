# ------- Inicialización de la aplicación Flask y sus extensiones -------

from flask import Flask, render_template, request, session, redirect, url_for, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_migrate import Migrate
from flasgger import Swagger
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import redis

from app.config import config
from app.models import db

migrate = Migrate()
csrf = CSRFProtect()
swagger = Swagger()
redis_client = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Crear la aplicación Flask 
def create_app(config_name='default'):

    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, '..', 'templates'),
        static_folder=os.path.join(BASE_DIR, '..', 'static')
)
    
    # Cargar la configuración
    app.config.from_object(config[config_name])

    # Mostrar configuración clave en consola
    print(f"DATABASE_URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    print(f"REDIS_URL: {app.config.get('REDIS_URL')}")

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Redis para manejo de sesiones
    global redis_client
    try:
        redis_client = redis.from_url(app.config['REDIS_URL'], decode_responses=True)
        redis_client.ping()
        print("✅ Redis conectado correctamente")
    except Exception as e:
        print(f"⚠️  Redis no disponible: {e}")
        redis_client = None
    
    # Swagger para documentación de la API
    swagger_template = {

    "swagger": "2.0",

    "info": {
        "title": "API REST - Práctica 2",
        "description": "API con JWT, SQLAlchemy y Flask",
        "version": "1.0.0"
        
    }, #  Definir que se necesita autenticación Bearer para toda la API

    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header usando el esquema Bearer. Ejemplo: 'Bearer {token}'"
        }
    },

    "security": [
        {
            "Bearer": []
        }
    ]
}

    # swagger_template = {

    #     "swagger": "2.0",

    #     "info": {
    #         "title": "API REST - Práctica 2",
    #         "description": "API con JWT, SQLAlchemy y Flask",
    #         "version": "1.0.0"
    #     },

    #     "securityDefinitions": {
    #         "Bearer": {
    #             "type": "apiKey",
    #             "name": "Authorization",
    #             "in": "header",
    #             "description": "JWT Authorization header usando el esquema Bearer. Ejemplo: 'Bearer {token}'"
    #         }
    #     }
    # }
    
    Swagger(app, template=swagger_template) # Inicializar Swagger

    # Proxy fix (NGINX)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)  
    print(" ProxyFix configurado")

    # Registrar blueprints API
    from app.routes.usuarios import bp as usuarios_bp
    from app.routes.productos import bp as productos_bp
    
    csrf.exempt(usuarios_bp)
    csrf.exempt(productos_bp)

    app.register_blueprint(usuarios_bp, url_prefix='/api')
    app.register_blueprint(productos_bp, url_prefix='/api')
    
    # Registrar rutas legacy (tus rutas HTML originales)
    register_legacy_routes(app)
    
    # Manejadores de errores
    register_error_handlers(app)
    
    return app

# Rutas legacy (HTML)
def register_legacy_routes(app):

    from app.models import User # Importar modelos necesarios
    from app.utils import token_requerido, generar_jwt, admin_requerido, get_real_scheme

    @app.route("/", methods=["GET"]) # Ruta raíz
    def root():
        return render_template("index.html")

    # Ruta de registro de usuarios
    @app.route("/register", methods=["GET", "POST"])

    def register():

        if request.method == "POST": # Manejar formulario de registro
            username = request.form.get("username")
            password = request.form.get("password")
            email = request.form.get("email")
            
            if not username or not password: # Verificar datos obligatorios
                return render_template("register.html", error="Faltan datos")
            
            # Verificar si el usuario ya existe
            if User.query.filter_by(username=username).first():
                return render_template("register.html", error="El usuario ya existe")
            
            # Crear nuevo usuario
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            return render_template("register.html", success="Usuario creado correctamente")
        
        return render_template("register.html")
    
    @app.route('/usuarios/panel')
    def panel_usuarios():
     return render_template('usuarios.html')
    
    # Ruta de login de usuarios
    @app.route("/login", methods=["POST", "GET"])
    def login():

        if request.method == "POST": # Manejar formulario de login
            username = request.form.get("username")
            password = request.form.get("password")
            
            user = User.query.filter_by(username=username).first() # Buscar usuario en la base de datos
            
            if user and user.check_password(password):
                # Generar token JWT
                token = generar_jwt(
                    user.username,
                    user.role,
                    app.config['JWT_SECRET'],
                    app.config['JWT_ALGORITHM'],
                    app.config['JWT_EXPIRATION_HOURS']
                )
                respuesta = redirect(url_for('seguro'))
                respuesta.set_cookie("token", token, httponly=True, 
                                   secure=app.config['IS_PRODUCTION'], 
                                   samesite='Lax')
                return respuesta
            
            else: # Usuario o contraseña incorrectos
                return render_template("login.html", error="Usuario o contraseña incorrectos")
        
        return render_template("login.html")
    
    # Ruta para el logout de usuarios
    @app.route("/logout", methods=["POST", "GET"])
    def logout():
        user = session.get("user", "Usuario")
        session.clear()
        response = make_response(render_template("logout.html", 
                                                message=f"Sesión de {user} cerrada correctamente"))
        response.set_cookie('token', '', expires=0)
        return response
    
    # Ruta insegura que expone información sensible
    @app.route("/inseguro") 
    def inseguro():
        scheme = get_real_scheme()
        user_agent = request.headers.get('User-Agent', 'Desconocido')
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        sensitive_info = {
            "scheme": scheme,
            "ip_cliente": ip,
            "user_agent": user_agent,
            "session_data": dict(session) if session else "Sin sesión",
            "headers_completos": dict(request.headers),
            "secret_key_hint": app.config['SECRET_KEY'][:8] + "...",
            "server_info": f"Python Flask en {request.host}"
        }
        
        return render_template("inseguro.html", scheme=scheme.upper(), sensitive_info=sensitive_info,
            vulnerabilities=[
                "✗ Accesible por HTTP (sin cifrado)",
                "✗ No requiere autenticación", 
                "✗ Expone información del sistema",
                "✗ Muestra headers y datos internos"
            ])
    
    # Ruta segura que requiere autenticación
    @app.route("/seguro")
    @token_requerido

    def seguro():

        scheme = get_real_scheme() # Obtener el esquema real (http o https)
        if app.config['IS_PRODUCTION'] and scheme != "https": # Redirigir a HTTPS en producción
            return redirect(request.url.replace("http://", "https://", 1), code=301)
        
        user = request.user # Obtener el usuario del request (establecido por el decorador)
        response = make_response(render_template("seguro.html", user=user, scheme=scheme.upper()))
        
        # Headers de seguridad
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        if scheme == "https":
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response

    # Ruta protegida para usuarios autenticados
    @app.route("/api/usuario/protegido", methods=["GET"])
    @token_requerido

    def usuario_protegido():
        username = request.user
        user = User.query.filter_by(username=username).first()
        
        if user:
            return render_template("usuario_protegido.html", username=user.username, role=user.role)
        else:
            return render_template("usuario_protegido.html", username="Desconocido", role="N/A")
        
    # Ruta para listar todos los usuarios (solo admin)
    @app.route("/api/usuario/listar", methods=["GET"])
    @admin_requerido

    def listar_usuarios():
        users = User.query.all()
        usuarios = [{'username': u.username, 'role': u.role} for u in users]
        return render_template("listar_usuarios.html", usuarios=usuarios, total=len(usuarios))

# Manejadores de errores 
def register_error_handlers(app):
    
    @app.errorhandler(401)
    def error_401(error):
        return jsonify({'error': 'No autenticado'}), 401
    
    @app.errorhandler(403)
    def error_403(error):
        return jsonify({'error': 'Acceso denegado'}), 403
    
    @app.errorhandler(404)
    def error_404(error):
        return jsonify({'error': 'Recurso no encontrado'}), 404