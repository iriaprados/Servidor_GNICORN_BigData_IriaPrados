# ------  Rutas relacionadas con la gestión de usuarios ------

from flask import Blueprint, request, jsonify, current_app
from marshmallow import ValidationError
from app.models import db, User
from app.schemas import user_schema, users_schema, user_update_schema
from app.utils import generar_jwt, token_requerido, admin_requerido
import json

bp = Blueprint('usuarios', __name__) # Crear un blueprint para las rutas de usuarios

# Registros de usuarios via API
@bp.route('/usuarios/register', methods=['POST'])
def register_api():
    
    try: # Validar y deserializar los datos de entrada
        data = user_schema.load(request.json)

    except ValidationError as err:# Si hay errores de validación, devolverlos
        return jsonify({"errors": err.messages}), 400
    
    if User.query.filter_by(username=data['username']).first(): # Verificar si el usuario ya existe
        return jsonify({"error": "El usuario ya existe"}), 400
    
    # Crear nuevo usuario
    user = User(username=data['username'], email=data.get('email'))
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    
    return jsonify({"message": "Usuario creado", "user": user.to_dict()}), 201

# Login de usuarios via API
@bp.route('/usuarios/login', methods=['POST'])
def login_api():
    
    data = request.json # Obtener datos de la solicitud
    if not data: # Si no se enviaron datos
        return jsonify({"error": "No se enviaron datos"}), 400
    
    # Obtener y verificar credenciales
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password: # Verificar que se proporcionen ambos campos
        return jsonify({"error": "Faltan campos requeridos"}), 400
    
    user = User.query.filter_by(username=username).first() # Buscar usuario en la base de datos
    
    if not user or not user.check_password(password): # Verificar credenciales
        return jsonify({"error": "Credenciales inválidas"}), 401
    
    token = generar_jwt( # Generar token JWT
        user.username,
        user.role,
        current_app.config['JWT_SECRET'],
        current_app.config['JWT_ALGORITHM'],
        current_app.config['JWT_EXPIRATION_HOURS']
    )
    
    return jsonify({
        "access_token": token,
        "user": user.to_dict()
    }), 200

# Listar todos los usuarios (solo admin)
@bp.route('/usuarios', methods=['GET'])
@admin_requerido

def get_usuarios():
  
    # Intentar usar caché de Redis
    from app import redis_client
    cache_key = "usuarios:all"
    
    if redis_client: 

        try: # Leer desde caché
            cached = redis_client.get(cache_key)
            if cached:
                print("Datos obtenidos desde caché Redis")
                return jsonify(json.loads(cached)), 200
            
        except Exception as e: # Error al leer desde Redis
            print(f"Error al leer de Redis: {e}")
    
    # Si no hay caché, consultar BD
    users = User.query.all()
    result = users_schema.dump(users)
    
    # Guardar en caché por 5 minutos
    if redis_client:
        try:
            redis_client.setex(cache_key, 300, json.dumps(result))
            print(" Datos guardados en caché Redis")
        except Exception as e:
            print(f"Error al escribir en Redis: {e}")
    
    return jsonify(result), 200

# Obtener un usuario por ID
@bp.route('/usuarios/<int:id>', methods=['GET'])
@token_requerido

def get_usuario(id):
    user = User.query.get_or_404(id) # Buscar usuario por ID o devolver 404
    return jsonify(user.to_dict()), 200 

# Actualizar un usuario por ID
@bp.route('/usuarios/<int:id>', methods=['PUT'])
@token_requerido

def update_usuario(id):

    user = User.query.get_or_404(id) # Buscar usuario por ID o devolver 404
    
    # Solo admins o el propio usuario pueden actualizar
    if request.role != 'admin' and request.user != user.username:
        return jsonify({"error": "No tienes permiso"}), 403
    
    try: # Validar y deserializar los datos de entrada
        data = user_update_schema.load(request.json, partial=True)
    except ValidationError as err: # Si hay errores de validación, devolverlos
        return jsonify({"errors": err.messages}), 400
    
    # Actualizar campos del usuario
    if 'username' in data:
        user.username = data['username']
    if 'email' in data:
        user.email = data['email']
    if 'password' in data:
        user.set_password(data['password'])
    
    db.session.commit() # Guardar cambios en la base de datos
    
    # Invalidar caché
    from app import redis_client
    if redis_client:
        try:
            redis_client.delete("usuarios:all")
        except:
            pass
    
    return jsonify({"message": "Usuario actualizado", "user": user.to_dict()}), 200

# Eliminar un usuario por ID (solo admin)
@bp.route('/usuarios/<int:id>', methods=['DELETE'])
@admin_requerido

def delete_usuario(id):
    
    user = User.query.get_or_404(id) # Buscar usuario por ID o devolver 404
    db.session.delete(user) # Eliminar usuario de la base de datos
    db.session.commit() # Guardar cambios
    
    # Invalidar caché
    from app import redis_client
    if redis_client:
        try:
            redis_client.delete("usuarios:all")
        except:
            pass
    
    return jsonify({"message": "Usuario eliminado"}), 200

# Ruta protegida de ejemplo
@bp.route('/usuarios/privado', methods=['GET'])
@token_requerido

def privado():
    return jsonify({
        "msg": "Acceso autorizado", 
        "user": request.user,
        "role": request.role
    }), 200