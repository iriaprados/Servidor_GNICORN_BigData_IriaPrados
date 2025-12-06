# ------- Utilidades para manejo de JWT y protección de rutas -------

import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify

# Generar un token JWT
def generar_jwt(username, role, secret, algorithm, hours): 
 
    payload = { # Datos del token
        "user": username,
        "role": role,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=hours)
    }
    return jwt.encode(payload, secret, algorithm=algorithm)

# Verificar un token JWT
def verificar_jwt(token, secret, algorithm):
    
    try: # Decodificar el token
        payload = jwt.decode(token, secret, algorithms=[algorithm])
        return payload, 200
    
    except jwt.ExpiredSignatureError: 
        return {"error": "Token expirado"}, 401
    
    except jwt.InvalidTokenError:
        return {"error": "Token inválido"}, 401

# Decorador para proteger rutas con JWT
def token_requerido(f):
    @wraps(f)

    def decorador(*args, **kwargs):

        token = request.headers.get('Authorization') # Obtener el token del encabezado Authorization

        if token: # Si el token está en el encabezado Authorization
            try:
                token = token.split(" ")[1]  # Formato "Bearer <token>"
            except IndexError:
                return jsonify({"error": "Formato de token inválido"}), 401
            
        else: # Si no está en el encabezado, buscar en las cookies
            token = request.cookies.get('token')
            if not token:
                return jsonify({"error": "Token es requerido"}), 401

        from flask import current_app # Importar current_app para acceder a la configuración de la aplicación
        payload, status = verificar_jwt(
            token, 
            current_app.config['JWT_SECRET'],
            current_app.config['JWT_ALGORITHM']
        )
        
        if "error" in payload: # Si hay un error en la verificación del token
            return jsonify(payload), status

        request.user = payload["user"]
        request.role = payload["role"]
        return f(*args, **kwargs)
    
    return decorador

# Verificar si el usuario tiene el rol requerido
def admin_requerido(f):
    @wraps(f)

    def decorador(*args, **kwargs):

        token = request.headers.get('Authorization') # Obtener el token del encabezado Authorization

        if token: # Si el token está en el encabezado Authorization
            try:
                token = token.split(" ")[1]
            except IndexError:
                return jsonify({"error": "Formato de token inválido"}), 401
        
        else: # Si no está en el encabezado, buscar en las cookies
            token = request.cookies.get('token')
            if not token:
                return jsonify({"error": "Token es requerido"}), 401

        from flask import current_app # Importar current_app para acceder a la configuración de la aplicación
        
        payload, status = verificar_jwt( # Verificar el token
            token,
            current_app.config['JWT_SECRET'],
            current_app.config['JWT_ALGORITHM']
        )
        
        if "error" in payload:
            return jsonify(payload), status

        if payload.get("role") != "admin":
            return jsonify({"error": "Acceso denegado, solo administradores"}), 403

        request.user = payload["user"] # Asignar el usuario y rol al objeto request
        request.role = payload["role"] # Asignar el usuario y rol al objeto request

        return f(*args, **kwargs)
    
    return decorador

def get_real_scheme(): # Obtener el esquema real (http o https) considerando proxies
    return request.headers.get("X-Forwarded-Proto", request.scheme).lower()