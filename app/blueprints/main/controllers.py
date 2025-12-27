#---- Controladores principales de la aplicación -----

from flask import render_template, request, redirect, make_response, session, current_app
from app.models import User
from app.utils import get_real_scheme

class MainController:
    
    # Página principal
    @staticmethod
    def index():
        return render_template("index.html")
    
    # Endpoint inseguro (sin autenticación)
    @staticmethod
    def inseguro():

        scheme = get_real_scheme()
        user_agent = request.headers.get('User-Agent', 'Desconocido')
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        # Información sensible expuesta
        sensitive_info = {
            "scheme": scheme,
            "ip_cliente": ip,
            "user_agent": user_agent,
            "session_data": dict(session) if session else "Sin sesión",
            "headers_completos": dict(request.headers),
            "secret_key_hint": current_app.config['SECRET_KEY'][:8] + "...",
            "server_info": f"Python Flask en {request.host}"
        }
        
        # Renderizar la plantilla con la información sensible
        return render_template("inseguro.html", scheme=scheme.upper(), 
                             sensitive_info=sensitive_info,
                             vulnerabilities=[
                                 "✗ Accesible por HTTP (sin cifrado)",
                                 "✗ No requiere autenticación", 
                                 "✗ Expone información del sistema",
                                 "✗ Muestra headers y datos internos"
                             ])
    
    # Endpoint seguro (requiere autenticación)
    @staticmethod
    def seguro():

        scheme = get_real_scheme() # Detectar esquema real detrás de proxies
        if current_app.config['IS_PRODUCTION'] and scheme != "https": # Forzar HTTPS en producción
            return redirect(request.url.replace("http://", "https://", 1), code=301)
        
        user = request.user
        response = make_response(render_template("seguro.html", user=user, scheme=scheme.upper()))
        
        # Headers de seguridad
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        if scheme == "https":
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response
    
    # Perfil protegido con JWT
    @staticmethod
    def usuario_protegido():
    
        username = request.user
        user = User.query.filter_by(username=username).first()
        
        if user:
            return render_template("usuario_protegido.html", 
                                 username=user.username, role=user.role)
        else:
            return render_template("usuario_protegido.html", 
                                 username="Desconocido", role="N/A")
        
    # Listar todos los usuarios (solo admin)
    @staticmethod
    def listar_usuarios():
        
        users = User.query.all()
        usuarios = [{'username': u.username, 'role': u.role} for u in users]
        return render_template("listar_usuarios.html", usuarios=usuarios, total=len(usuarios))