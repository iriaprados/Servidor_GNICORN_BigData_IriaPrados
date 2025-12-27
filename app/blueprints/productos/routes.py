# ----- Rutas de productos -----


from flask import request, jsonify
from flasgger import swag_from
from . import bp
from .controllers import ProductoController
from app.utils import token_requerido

#  CREAR PRODUCTO 
@bp.route('/productos', methods=['POST'])
@token_requerido

@swag_from({
    'tags': ['Productos'],
    'summary': 'Crear un nuevo producto',
    'security': [{'Bearer': []}],
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'required': ['nombre', 'precio'],
            'properties': {
                'nombre': {'type': 'string', 'example': 'Laptop HP'},
                'descripcion': {'type': 'string', 'example': 'Laptop gaming 16GB RAM'},
                'precio': {'type': 'number', 'example': 899.99},
                'stock': {'type': 'integer', 'example': 10}
            }
        }
    }],

    'responses': {
        201: {
            'description': 'Producto creado exitosamente',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'producto': {'type': 'object'}
                }
            }
        },

        400: {'description': 'Error de validación'},
        401: {'description': 'No autenticado'},
        404: {'description': 'Usuario no encontrado'}
    }
})
def create_producto():
    return ProductoController.create_producto()


#  LISTAR PRODUCTOS 
@bp.route('/productos', methods=['GET'])

@swag_from({
    'tags': ['Productos'],
    'summary': 'Listar todos los productos',
    'responses': {
        200: {
            'description': 'Lista de productos',
            'schema': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'nombre': {'type': 'string'},
                        'descripcion': {'type': 'string'},
                        'precio': {'type': 'number'},
                        'stock': {'type': 'integer'},
                        'user_id': {'type': 'integer'},
                        'created_at': {'type': 'string'}
                    }
                }
            }
        }
    }
})

def get_productos():
    return ProductoController.get_productos()


#  OBTENER PRODUCTO POR ID 
@bp.route('/productos/<int:id>', methods=['GET'])

@swag_from({
    'tags': ['Productos'],
    'summary': 'Obtener un producto por ID',
    'parameters': [{
        'name': 'id',
        'in': 'path',
        'type': 'integer',
        'required': True,
        'description': 'ID del producto'
    }],

    'responses': {
        200: {
            'description': 'Producto encontrado',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'nombre': {'type': 'string'},
                    'descripcion': {'type': 'string'},
                    'precio': {'type': 'number'},
                    'stock': {'type': 'integer'},
                    'user_id': {'type': 'integer'},
                    'created_at': {'type': 'string'}
                }
            }
        },

        404: {'description': 'Producto no encontrado'}
    }
})
def get_producto(id):
    return ProductoController.get_producto(id)


#  ACTUALIZAR PRODUCTO 
@bp.route('/productos/<int:id>', methods=['PUT'])
@token_requerido

@swag_from({
    'tags': ['Productos'],
    'summary': 'Actualizar un producto',
    'security': [{'Bearer': []}],
    'parameters': [

        {
            'name': 'id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID del producto'
        },

        {
            'name': 'body',
            'in': 'body',
            'schema': {
                'type': 'object',
                'properties': {
                    'nombre': {'type': 'string', 'example': 'Laptop Dell'},
                    'descripcion': {'type': 'string', 'example': 'Laptop actualizada'},
                    'precio': {'type': 'number', 'example': 799.99},
                    'stock': {'type': 'integer', 'example': 5}
                }
            }
        }
    ],

    'responses': {
        200: {
            'description': 'Producto actualizado',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'producto': {'type': 'object'}
                }
            }
        },

        400: {'description': 'Error de validación'},
        401: {'description': 'No autenticado'},
        403: {'description': 'No tienes permiso'},
        404: {'description': 'Producto no encontrado'}
    }
})

def update_producto(id):
    return ProductoController.update_producto(id)


#  ELIMINAR PRODUCTO 
@bp.route('/productos/<int:id>', methods=['DELETE'])
@token_requerido

@swag_from({
    'tags': ['Productos'],
    'summary': 'Eliminar un producto',
    'security': [{'Bearer': []}],
    'parameters': [{
        'name': 'id',
        'in': 'path',
        'type': 'integer',
        'required': True,
        'description': 'ID del producto a eliminar'
    }],

    'responses': {
        200: {
            'description': 'Producto eliminado',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'}
                }
            }
        },

        401: {'description': 'No autenticado'},
        403: {'description': 'No tienes permiso'},
        404: {'description': 'Producto no encontrado'}
    }
})

def delete_producto(id):
    return ProductoController.delete_producto(id)


#  PRODUCTOS POR USUARIO 
@bp.route('/productos/usuario/<int:user_id>', methods=['GET'])

@swag_from({
    'tags': ['Productos'],
    'summary': 'Obtener productos de un usuario específico',
    'parameters': [{
        'name': 'user_id',
        'in': 'path',
        'type': 'integer',
        'required': True,
        'description': 'ID del usuario'
    }],

    'responses': {
        200: {
            'description': 'Productos del usuario',
            'schema': {
                'type': 'object',
                'properties': {
                    'user': {'type': 'string'},
                    'productos': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'nombre': {'type': 'string'},
                                'descripcion': {'type': 'string'},
                                'precio': {'type': 'number'},
                                'stock': {'type': 'integer'},
                                'user_id': {'type': 'integer'},
                                'created_at': {'type': 'string'}
                            }
                        }
                    },

                    'total': {'type': 'integer'}
                }
            }
        },

        404: {'description': 'Usuario no encontrado'}
    }
})

def get_productos_usuario(user_id):
    return ProductoController.get_productos_usuario(user_id)