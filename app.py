from flask import Flask, request, session, jsonify, redirect, url_for, make_response, render_template
from datetime import timedelta
from werkzeug.middleware.proxy_fix import ProxyFix



app = Flask(__name__)

app.secret_key = 'claveSecreta' # Clave secreta para la sesión
app.permanent_session_lifetime = timedelta(minutes=30) # Duración de la sesión, después de 30 minutos de inactividad

# Flags de cookie y lifetime (evita manejarlo “a mano”)
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
)

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

# Iniciar sesión 
@app.route("/login", methods=["POST", "GET"]) 
def login():
    if request.method == "POST":
        user = request.form.get("user") # Obtener el nombre de usuario del formulario
        if not user:
            return "Se necesita un nombre de usuario", 400
        session.permanent = True
        session["user"] = user
        return render_template("login.html", user=user) # Redirigir a la página segura después del login
    return render_template("login.html")
    
    # # Alternativa: configurar en app.config: SESSION_COOKIE_SECURE=True, etc.
    # return cookie_flags(resp)

# Cerrar sesión
@app.route("/logout", methods=["POST", "GET"]) 
def logout():
    if request.method == "POST":
        session.clear()
        return render_template("logout.html", message="Sesión cerrada correctamente") # Redirigir a la página de logout
    return render_template("logout.html")
        
 # Iniciar sesión no es necesario, metodo HTTP o HTTPS
@app.route("/inseguro")
def inseguro():
    return render_template("inseguro.html")
    # """
    # Información expuesta sin autenticación ni TLS garantizado
    # """
    # return jsonify({
    #     "debug": True,
    #     "message": "Este endpoint no requiere sesión y puede ir por HTTP."
    # })

# Iniciar sesión y usar HTTPS
@app.route("/seguro") 
def seguro():
    if "user" not in session:
        return "Acceso no autorizado. Debe de iniciar sesión.", 401
    
    # Forzar HTTPS (directo o detrás de NGINX)
    scheme = request.headers.get("X-Forwarded-Proto", request.scheme)
    if scheme != "https":
        return "Use HTTPS para este recurso.", 400
    return render_template("seguro.html", user=session["user"])













    # """
    # Requiere sesión y pretende servirse solo por HTTPS
    # """
    # if "user" not in session:
    #     return jsonify({"error": "unauthorized"}), 401
    
    # # (Opcional) Comprobar esquema si el proxy pasa X-Forwarded-Proto
    # scheme = request.headers.get("X-Forwarded-Proto", request.scheme)
    # if scheme != "https":
    #     return jsonify({"error": "use https"}), 400
    
    # return jsonify({
    #     "secret": "contenido solo para usuarios autenticados por HTTPS",
    #     "user": session["user"]



# Ejecutar la aplicación
if __name__ == "__main__":
    app.secret_key = 'claveSecreta' # Clave secreta para la sesión
    app.run(debug=True, host="0.0.0.0", port=8080)

