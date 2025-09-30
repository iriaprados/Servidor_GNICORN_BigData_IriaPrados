from flask import Flask, request, session, jsonify, redirect, url_for, make_response, render_template
from datetime import timedelta
from werkzeug.middleware.proxy_fix import ProxyFix 
import sqlite3 # Importar la base de datos SQLite
import os
from werkzeug.security import generate_password_hash, check_password_hash # Para el hasheo de las contraseñas
from flask_wtf import CSRFProtect

# Configuración de la base de datos SQLite y de la aplicación Flask
user_db = "users.db"
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "claveSecretaLocal")  # usa var de entorno en producción
app.permanent_session_lifetime = timedelta(minutes=30) 

# RF2: Protección CSRF
csrf = CSRFProtect(app)
app.permanent_session_lifetime = timedelta(minutes=30)

# Conexión con la base de datos y creación de las tablas
def init_db():
    conn = sqlite3.connect(user_db)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Flags de cookie y lifetime (evita manejarlo “a mano”)
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
)

# Permitir el uso de cookies seguras en https
if os.environ.get("FLASK_ENV") == "production":# Solo se usa la cookie si se usa un protocolo https
    app.config["SESSION_COOKIE_SECURE"] = True
else:
    app.config["SESSION_COOKIE_SECURE"] = False


# Respetar cabeceras del proxy (X-Forwarded-Proto)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)


def cookie_flags(resp):
    """
    Forzar flags en cookies de sesión si el servidor está detrás de HTTPS.
    En desarrollo, podéis parametrizar por entorno o encabezado X-Forwarded-Proto.
    """
    # En Flask, usa SESSION_COOKIE_* en config para hacerlo global
    return resp


# Página inicial
@app.route("/", methods=["GET"])
def root():
    return render_template("index.html")


# Registro de usuarios
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
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


# Iniciar sesión 
@app.route("/login", methods=["POST", "GET"]) 
def login():
    if request.method == "POST":
        username = request.form.get("username") 
        password= request.form.get("password")

        # Conectar con la base de datos del usuario
        conn = sqlite3.connect(user_db)
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM users WHERE username=?", (username,))
        row = cur.fetchone()
        conn.close()

        if row and check_password_hash(row[0], password): 
            session["user"] = username
            return render_template("seguro.html") # Se ha introducido correctamente los datos de la sesión
        else:
            return render_template("login.html", error="Usuario o contraseña incorrectos")
        
    return render_template("login.html")
    
    # # Alternativa: configurar en app.config: SESSION_COOKIE_SECURE=True, etc.
    # return cookie_flags(resp)

# Cerrar sesión
@app.route("/logout", methods=["POST", "GET"])
def logout():
    session.clear()
    return render_template("logout.html", message="Sesión cerrada correctamente")

        
 # Iniciar sesión no es necesario, metodo HTTP o HTTPS
@app.route("/inseguro")
def inseguro():
    return render_template("inseguro.html")


# Iniciar sesión y usar HTTPS
@app.route("/seguro")
def seguro():
    if "user" not in session:
        return render_template("noauth.html"), 401  

    # RF2: Forzar HTTPS solo en producción
    if os.environ.get("FLASK_ENV") == "production": # SI el entorno está en producción
        scheme = request.headers.get("X-Forwarded-Proto", request.scheme) # Comprobar el esquema, http o https
        if scheme != "https": # Si no es HTTPS
            url = request.url.replace("http://", "https://", 1) # Redirigir a la versión HTTPS, para fallo de seguridad
            return redirect(url, code=301) # Se ejecuta la redirección a HTTPS

    return render_template("seguro.html", user=session["user"])


# Ejecutar la aplicación
if __name__ == "__main__":
    # app.secret_key = 'claveSecreta' # Clave secreta para la sesión
    app.run(debug=True, host="127.0.0.1", port=8000)

