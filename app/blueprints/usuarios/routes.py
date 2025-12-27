# ---- Rutas de usuarios ----

from flask import request, jsonify
from flasgger import swag_from
from . import bp
from .controllers import UsuarioController
from app.utils import token_requerido, admin_requerido
from app.cache import cache_result

# Registro de usuario
@bp.route('/usuarios/register', methods=['POST'])

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

def register_api():
    return UsuarioController.register()


# Login
@bp.route('/usuarios/login', methods=['POST'])

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

def login_api():
    return UsuarioController.login()


# Listar todos los usuarios (requiere admin)
@bp.route('/usuarios', methods=['GET'])
@admin_requerido
@cache_result(key_prefix="usuarios:all", ttl=300)

@swag_from({
    'tags': ['Usuarios'],
    'summary': 'Listar todos los usuarios (requiere admin)',
    'security': [{'Bearer': []}],
    'responses': {
        200: {'description': 'Lista de usuarios'},
        403: {'description': 'Acceso denegado'}
    }
})

def get_usuarios():
    return UsuarioController.get_usuarios()


# Obtener usuario por ID
@bp.route('/usuarios/<int:id>', methods=['GET'])
@token_requerido

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
    return UsuarioController.get_usuario(id)


# Actualizar usuario por ID
@bp.route('/usuarios/<int:id>', methods=['PUT'])
@token_requerido

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

def update_usuario(id):
    return UsuarioController.update_usuario(id)


# Eliminar usuario por ID
@bp.route('/usuarios/<int:id>', methods=['DELETE'])
@admin_requerido

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
    return UsuarioController.delete_usuario(id)


#Enpoint privado de prueba
@bp.route('/usuarios/privado', methods=['GET'])
@token_requerido

@swag_from({
    'tags': ['Usuarios'],
    'summary': 'Endpoint de prueba protegido con JWT',
    'security': [{'Bearer': []}],
    'responses': {

        200: {'description': 'Acceso autorizado'},
        401: {'description': 'Token requerido o inválido'}
    }
})

def privado():
    return UsuarioController.privado()


# Estadísticas de la caché
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

def cache_stats():
    return UsuarioController.cache_stats()


# Limipiar toda la caché
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

def clear_cache():
    return UsuarioController.clear_cache()