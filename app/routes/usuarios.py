# ------  Rutas relacionadas con la gestión de usuarios ------

from flask import Blueprint, request, jsonify, current_app, render_template
from marshmallow import ValidationError
from flasgger import swag_from 
from app.models import db, User
from app.schemas import user_schema, users_schema, user_update_schema
from app.utils import generar_jwt, token_requerido, admin_requerido
from app.cache import cache_result, invalidate_cache # Importar funciones de caché
import json

bp = Blueprint('usuarios', __name__) # Crear un blueprint para las rutas de usuarios



# Registros de usuarios via API
@bp.route('/usuarios/register', methods=['POST'])

# Documentación Swagger para la ruta de registro
@swag_from({

    'tags': ['Usuarios'],
    'summary': 'Registrar un nuevo usuario',
    'parameters': [{

        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {

            'type': 'object',
            'required': ['username', 'password'],
            'properties': {

                'username': {'type': 'string', 'example': 'juan'},
                'email': {'type': 'string', 'example': 'juan@example.com'},
                'password': {'type': 'string', 'example': '1234'}
            }
        }
    }],

    'responses': {
        201: {'description': 'Usuario creado exitosamente'},
        400: {'description': 'Error de validación'}
    }

})

# Registro de usuario
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
# Documentación Swagger para la ruta de login
@swag_from({ 

    'tags': ['Usuarios'],
    'summary': 'Iniciar sesión y obtener token JWT',
    'parameters': [{

        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {

            'type': 'object',
            'required': ['username', 'password'],
            'properties': {

                'username': {'type': 'string', 'example': 'miusuario'},
                'password': {'type': 'string', 'example': '1234'}
            }
        }
    }],

    'responses': {
        200: {
            'description': 'Token JWT generado',
            'schema': {
                'type': 'object',
                'properties': {
                    'access_token': {'type': 'string'},
                    'user': {'type': 'object'}
                }
            }
        },
        401: {'description': 'Credenciales inválidas'}
    }
})

# Login de usuario
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
@cache_result(key_prefix="usuarios:all", ttl=300) # Almacenar en caché por 5 minutos

# Documentación Swagger para la ruta de listar usuarios
@swag_from({ 
    'tags': ['Usuarios'],
    'summary': 'Listar todos los usuarios (requiere admin)',
    'security': [{'Bearer': []}],
    'responses': {
        200: {'description': 'Lista de usuarios'},
        403: {'description': 'Acceso denegado'}
    }
})

# Obtener todos los usuarios
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

# Documentación Swagger para la ruta de obtener usuario por ID
@swag_from({  

    'tags': ['Usuarios'],
    'summary': 'Obtener un usuario por ID',
    'security': [{'Bearer': []}],
    'parameters': [{

        'name': 'id',
        'in': 'path',
        'type': 'integer',
        'required': True,
        'description': 'ID del usuario'
    }],

    'responses': {
        200: {'description': 'Usuario encontrado'},
        404: {'description': 'Usuario no encontrado'}
    }
})

def get_usuario(id):
    user = User.query.get_or_404(id) # Buscar usuario por ID o devolver 404
    return jsonify(user.to_dict()), 200 

# Actualizar un usuario por ID
@bp.route('/usuarios/<int:id>', methods=['PUT'])
@token_requerido

# Documentación Swagger para la ruta de actualizar usuario
@swag_from({  

    'tags': ['Usuarios'],
    'summary': 'Actualizar un usuario',
    'security': [{'Bearer': []}],
    'parameters': [

        {
            'name': 'id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID del usuario'
        },

        {
            'name': 'body',
            'in': 'body',
            'schema': {

                'type': 'object',
                'properties': {

                    'username': {'type': 'string', 'example': 'nuevo_nombre'},
                    'email': {'type': 'string', 'example': 'nuevo@email.com'},
                    'password': {'type': 'string', 'example': 'nueva_pass'}
                }
            }
        }
    ],

    'responses': {
        200: {'description': 'Usuario actualizado'},
        403: {'description': 'No tienes permiso'},
        404: {'description': 'Usuario no encontrado'}
    }
})

# Actualizar usuario
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
    
    # Invalidar caché después de la actualización del write- through
    invalidate_cache("usuarios:*")  # Invalidate all user-related cache keys
    print(f" Usuario {id} actualizado, caché invalidado")
    
    return jsonify({"message": "Usuario actualizado", "user": user.to_dict()}), 200

# Eliminar un usuario por ID (solo admin)
@bp.route('/usuarios/<int:id>', methods=['DELETE'])
@admin_requerido

# Documentación Swagger para la ruta de eliminar usuario
@swag_from({  

    'tags': ['Usuarios'],
    'summary': 'Eliminar un usuario (requiere admin)',
    'security': [{'Bearer': []}],
    'parameters': [{

        'name': 'id',
        'in': 'path',
        'type': 'integer',
        'required': True,
        'description': 'ID del usuario a eliminar'
    }],

    'responses': {
        200: {'description': 'Usuario eliminado'},
        403: {'description': 'Acceso denegado'},
        404: {'description': 'Usuario no encontrado'}
    }
})

def delete_usuario(id):
    
    user = User.query.get_or_404(id) # Buscar usuario por ID o devolver 404
    db.session.delete(user) # Eliminar usuario de la base de datos
    db.session.commit() # Guardar cambios
    
    # Invalidar caché después de la eliminación del write-through
    invalidate_cache("usuarios:*")
    print(f" Usuario {id} eliminado, caché invalidado")
    
    return jsonify({"message": "Usuario eliminado"}), 200


# Ruta protegida de ejemplo
@bp.route('/usuarios/privado', methods=['GET'])
@token_requerido

# Documentación Swagger para la ruta privada
@swag_from({  

    'tags': ['Usuarios'],
    'summary': 'Endpoint de prueba protegido con JWT',
    'security': [{'Bearer': []}],
    'responses': {

        200: {'description': 'Acceso autorizado'},
        401: {'description': 'Token requerido o inválido'}
    }
})

# Endpoint privado de prueba
def privado():
    return jsonify({
        "msg": "Acceso autorizado", 
        "user": request.user,
        "role": request.role
    }), 200


# Endpoint privado de prueba de estadísticas de caché
@bp.route('/usuarios/cache/stats', methods=['GET'])
@admin_requerido

@swag_from({

    'tags': ['Usuarios'],
    'summary': 'Obtener estadísticas del sistema de caché (admin)',
    'security': [{'Bearer': []}],
    'responses': {

        200: {
            'description': 'Estadísticas de caché Redis',
            'schema': {
                'type': 'object',
                'properties': {
                    'application_stats': {'type': 'object'},
                    'redis_stats': {'type': 'object'},
                    'timestamp': {'type': 'string'}
                }
            }
        }
    }
})

# Endpoint de estadísticas de caché
def cache_stats():

    from flask import current_app
    
    if hasattr(current_app, 'cache_manager'): # Verificar si el cache_manager está disponible
        stats = current_app.cache_manager.get_stats() # Obtener estadísticas
        return jsonify(stats), 200 
    else:
        return jsonify({"error": "Cache manager no disponible"}), 503 # Servicio no disponible

# Limipiar toda la caché (solo admin)
@bp.route('/usuarios/cache/clear', methods=['POST'])
@admin_requerido

@swag_from({

    'tags': ['Usuarios'],
    'summary': 'Limpiar toda la caché (admin) - Usar con precaución',
    'security': [{'Bearer': []}],

    'responses': {
        200: {'description': 'Caché limpiado'},
        503: {'description': 'Redis no disponible'}
    }
})

# Endpoint para limpiar toda la caché
def clear_cache():
    invalidate_cache("*")
    return jsonify({"message": "Caché completamente limpiado"}), 200