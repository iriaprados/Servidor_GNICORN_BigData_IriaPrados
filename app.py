import token
from flask import Flask, request, session, jsonify, redirect, url_for, make_response, render_template
from datetime import timedelta
from werkzeug.middleware.proxy_fix import ProxyFix 
import sqlite3 # Importar la base de datos SQLite
import os
import jwt 
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash # Para el hasheo de las contraseñas
from flask_wtf import CSRFProtect #  Importar CSRFProtect para proteción de los métodos post 

# General: onfiguración de la base de datos SQLite y de la aplicación Flask
user_db = "users.db"
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "claveSecretaLocal")  # usa var de entorno en producción
app.permanent_session_lifetime = timedelta(minutes=30) 

# Práctica 2 RF2: condiguración con JWT
JWT_SECRET = os.environ.get("JWT_SECRET", "jwt_secret_key_local") # Clave secreta para JWT
JWT_ALGORITHM = "HS256" # Algorirmo de cifrado para JWT 
JWT_EXPIRATION_HOURS = 1 # Tiempo de expiración del token (1 hora)

# Práctica 1 - Opcional: Protección CSRF
csrf = CSRFProtect(app) # Inicializar CSRFProtect para proteger a todas las rutas que usan métodos POST

# Práctica 1: Configuración de cookies según entorno
is_production = os.environ.get("FLASK_ENV") == "production"

# Práctica 1 RF2: configuración de cookies seguras y uso de flags 
app.config.update(
    SESSION_COOKIE_SECURE=is_production,      # Solo HTTPS en producción
    SESSION_COOKIE_HTTPONLY=True,             # Protección XSS
    SESSION_COOKIE_SAMESITE="Lax",            # Protección CSRF
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30), # Duración de la sesión de la cookie 
)

# Práctica 1: Respetar cabeceras del proxy (X-Forwarded-Proto)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# General: Inicializar la base de datos si no existe
def init_db():
    conn = sqlite3.connect(user_db)
    cur = conn.cursor()
    
    # Crear la tabla si no existe
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    
    try: # Intentar añadir la columna 'role' si no existe
        cur.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    conn.close()

init_db()

# Práctica 2 RF2: Crear un usuario administrador para pruebas
conn = sqlite3.connect(user_db)
cur = conn.cursor()
cur.execute("UPDATE users SET role='admin' WHERE username='miusuario'")
conn.commit()
conn.close()


# Práctica 2 RF2: funciones para JWT (generar y validar el token)
# Función para generar el token JWT
def generar_jwt(username, role='user'): 

    payload={
        "user": username, # Nombre del usuario
        "role": role, # Rol del usuario
        "iat": datetime.utcnow(), # Fecha en el que se ha emitido el token
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS) # Cuando el token va a expirar
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM) # Devolver el token, con características definidas 

# Función para verificar el token JWT
def verificar_jwt(token): 
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM]) # Decodificar el token, si es valido
        return payload, 200
    except jwt.ExpiredSignatureError: # Si el token ha expirado, error
        return {"error": "Token expirado"}, 401
    except jwt.InvalidTokenError: # Si el token no es válido, error 
        return {"error": "Token inválido"}, 401

# Práctica 2 RF2: decoradores para proteger rutas con JWT
# Se necesita el token para acceder a la ruta
def token_requerido(f):
    @wraps(f)

    def decorador(*args, **kwargs):

        token = request.headers.get('Authorization') # Buscar el token en la cabecera Authorization
        if token:
            try:
                token = token.split(" ")[1]  # Formato "Bearer <token>"
            except IndexError:
                return jsonify({"error": "Formato de token inválido"}), 401
        else:
            token = request.cookies.get('token')  # Si no está en Authorization, buscar en cookie
            if not token:
                return jsonify({"error": "Token es requerido"}), 401

        payload, status = verificar_jwt(token)
        if "error" in payload:
            return jsonify(payload), status

        request.user = payload["user"]
        request.role = payload["role"]
        return f(*args, **kwargs)
    return decorador

# Se necesita ser administrador para acceder a la ruta
def admin_requerido(f):
    @wraps(f)

    def decorador(*args, **kwargs):

        token = request.headers.get('Authorization')
        if token:
            try:
                token = token.split(" ")[1]
            except IndexError:
                return jsonify({"error": "Formato de token inválido"}), 401
        else:
            token = request.cookies.get('token')
            if not token:
                return jsonify({"error": "Token es requerido"}), 401

        payload, status = verificar_jwt(token) # Verificar el token, si es válido, decodificarlo
        if "error" in payload:
            return jsonify(payload), status

        if payload.get("role") != "admin": # Si el rol no es admin, acceso denegado
            return jsonify({"error": "Acceso denegado, solo administradores"}), 403

        request.user = payload["user"]
        request.role = payload["role"]
        return f(*args, **kwargs)
    
    return decorador

# Práctica 1 RF5: función para obtener el esquema real (http o https)
def get_real_scheme(): # Obtener el esquema real considerando headers del proxy
    """Obtener el esquema real considerando headers del proxy"""
    return request.headers.get("X-Forwarded-Proto", request.scheme).lower()

# Página inicial - endpoint público sin autentificación
@app.route("/", methods=["GET"])
def root():
    return render_template("index.html")

# Registro de usuarios - endpoint público sin autentificación
@app.route("/register", methods=["GET", "POST"])
def register(): 

    if request.method == "POST": # Se envían los datos del formulario, usuario y contraseña
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password: 
            return render_template("register.html", error="Faltan datos")
        pw_hash = generate_password_hash(password)

        conn = sqlite3.connect(user_db) # Conexión con la base de datos 
        cur = conn.cursor()

        try:
            cur.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, pw_hash))
            conn.commit()
        except sqlite3.IntegrityError:
            return render_template("register.html", error="El usuario ya existe")
        finally:
            conn.close()
        return render_template("register.html", success="Usuario creado correctamente")
    
    return render_template("register.html")

# Iniciar sesión - endpoint público sin autentificación
@app.route("/login", methods=["POST", "GET"]) 
def login():

    if request.method == "POST":
        username = request.form.get("username") 
        password= request.form.get("password")

        conn = sqlite3.connect(user_db) 
        cur = conn.cursor()
        cur.execute("SELECT password_hash, role FROM users WHERE username=?", (username,))
        row = cur.fetchone()
        conn.close()

        if row and check_password_hash(row[0], password): 

            # Práctica 2 RF2: Generar el token JWT al iniciar sesión
            role = row[1] if row[1] else 'user' # Obtener el rol del usuario, por defecto 'user'
            token = generar_jwt(username, role) # Generar el token JWT
            respuesta = redirect(url_for('seguro')) # Respuesta con el token en la cabecera Authorization
            respuesta.set_cookie("token", token, httponly=True, secure=is_production, samesite='Lax') # Acceso a la cookie segura solo con https, con el token JWT guardado en la cookie
            return respuesta
        
        else: 
            return render_template("login.html", error="Usuario o contraseña incorrectos")
        
    return render_template("login.html")
    
    # session.permanent = True
    #         session["user"] = username
    #         return render_template("seguro.html", user=username) # Se ha introducido correctamente los datos de la sesión
    #     else:
    #         return render_template("login.html", error="Usuario o contraseña incorrectos")
        
    # return render_template("login.html")
    
    # # Alternativa: configurar en app.config: SESSION_COOKIE_SECURE=True, etc.
    # return cookie_flags(resp)

# Cerrar sesión
@app.route("/logout", methods=["POST","GET"])
def logout():

    user = session.get("user", "Usuario") # Obtener el usuario de la sesión
    session.clear() # Limpiar la sesión

    # Práctica 2 RF2: Eliminar la cookie del token JWT al cerrar sesión
    response = make_response(render_template("logout.html", message=f"Sesión de {user} cerrada correctamente"))
    response.set_cookie('token', '', expires=0) # Eliminar la cookie del token JWT
    return response

    # return render_template("logout.html", message=f"Sesión de {user} cerrada correctamente")

# Práctica 1 : endpoints seguros e inseguros
# Práctica 1 RF2: endpoint inseguro, iniciar sesión no es necesario, metodo HTTP o HTTPS
@app.route("/inseguro")
def inseguro():

    scheme = get_real_scheme() 
    user_agent = request.headers.get('User-Agent', 'Desconocido') # User-Agent del cliente
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)  # IP del cliente considerando proxy

    # Práctica 1 RF2: Información sensible expuesta (vulnerabilidad demostrada)
    sensitive_info = {
        "scheme": scheme,
        "ip_cliente": ip,
        "user_agent": user_agent,
        "session_data": dict(session) if session else "Sin sesión",
        "headers_completos": dict(request.headers),
        "secret_key_hint": app.secret_key[:8] + "...",
        "server_info": f"Python Flask en {request.host}"
    }

    # Práctica 1 RF2: Mostrar vulnerabilidades
    return render_template("inseguro.html", scheme=scheme.upper(), sensitive_info=sensitive_info,
        vulnerabilities=[
            " Accesible por HTTP (sin cifrado)",
            " No requiere autenticación", 
            " Expone información del sistema",
            " Muestra headers y datos internos"
            ])


# Práctica 1 RF2: endpoint seguro, iniciar sesión y usar HTTPS
@app.route("/seguro")
@token_requerido # Endpoint protegido, se necesita el token JWT para acceder
def seguro():

    # # Práctica 1 RF2: Verificar autenticación - ya no hace falta en la práctica 2, al usar JWT
    # if "user" not in session: # Si no hay usuario en la sesión, no está autenticado, no se puede acceder 
    #     return render_template("noauth.html"), 401

    # Práctica 1 RF5: Verificar HTTPS - Forzar siempre para endpoint seguro
    scheme = get_real_scheme()
    if is_production and scheme != "https": # En producción, si no es HTTPS, redirigir a HTTPS
        return redirect(request.url.replace("http://", "https://", 1), code=301)

    # Práctica 2 RF2: Obtener el usuario autenticado con JWT
    user = request.user # Obtener el usuario del token JWT
    response = make_response(render_template("seguro.html", user=user, scheme=scheme.upper()))

    # Práctica 1 RF2: Headers de seguridad adicionales
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # Práctica 1 RF5: HSTS solo en HTTPS
    if scheme == "https":
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains' 
    return response
    
# Práctica 2 RF2: endpoints adicionales protegidos con JWT
@app.route("/api/usuario/protegido",  methods=["GET"]) # Ruta para usuarios autenticados
@token_requerido # Endpoint protegido, se necesita el token JWT para acceder

def usuario_protegido(): # Endpoint protegido, se necesita el token JWT para acceder
    username = request.user

    conn = sqlite3.connect(user_db)
    cur = conn.cursor()
    cur.execute("SELECT username, role FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()

    if row:
        return render_template("usuario_protegido.html", username=row[0], role=row[1])
    else:
        return render_template("usuario_protegido.html", username="Desconocido", role="N/A")

@app.route("/api/usuario/listar", methods=["GET"]) # Ruta para administradores
@admin_requerido # Endpoint protegido, se necesita ser administrador para acceder

def listar_usuarios(): # Endpoint protegido, se necesita ser administrador para acceder

    conn = sqlite3.connect(user_db)
    cur = conn.cursor()
    cur.execute("SELECT username, role FROM users")
    rows = cur.fetchall()
    conn.close()

    usuarios = [{'id': r[0], 'username': r[1], 'role': r[2]} for r in rows] # Lista de usuarios con su rol
    return render_template("listar_usuarios.html", usuarios=usuarios, total=len(usuarios))

# Práctica 2 RF2: Manejo de errores
@app.errorhandler(401) # Error 401 - No autenticado
def error_401(error):
    return jsonify({'error': 'No autenticado'}), 401

@app.errorhandler(403) # Error 403 - Prohibido el acceso
def error_403(error):
    return jsonify({'error': 'Acceso denegado'}), 403

@app.errorhandler(404) # Error 404 - Información no encontrada
def error_404(error):
    return jsonify({'error': 'Recurso no encontrado'}), 404


# Ejecutar la aplicación
if __name__ == "__main__":
    # app.secret_key = 'claveSecreta' # Clave secreta para la sesión
    app.run(debug=True, host="127.0.0.1", port=8000)

