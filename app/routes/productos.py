# ------- Rutas relacionadas con productos -------

# Importaciones necesarias
from flask import Blueprint, request, jsonify, current_app
from marshmallow import ValidationError
from flasgger import swag_from
from app.models import db, User, Producto
from app.schemas import producto_schema, productos_schema
from app.utils import token_requerido, admin_requerido

bp = Blueprint('productos', __name__) # Blueprint para productos
 
# Listar todos los productos
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

# Crear producto
def create_producto():
  
    try: # Validar y deserializar los datos de entrada
        data = producto_schema.load(request.json)
    except ValidationError as err: # Si hay errores de validación, devolverlos
        return jsonify({"errors": err.messages}), 400
    
    # Obtener el usuario actual
    user = User.query.filter_by(username=request.user).first()
    if not user: 
        return jsonify({"error": "Usuario no encontrado"}), 404
    
    # Crear producto
    producto = Producto(
        nombre=data['nombre'],
        descripcion=data.get('descripcion'),
        precio=data['precio'],
        stock=data.get('stock', 0),
        user_id=user.id
    )
    
    # Guardar en la base de datos
    db.session.add(producto)
    db.session.commit()
    
    return jsonify({
        "message": "Producto creado",
        "producto": producto.to_dict()
    }), 201

# Listar todos los productos via API
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

# Listar todos los productos via API
def get_productos():
    productos = Producto.query.all() # Obtener todos los productos
    result = productos_schema.dump(productos) # Serializar los productos
    return jsonify(result), 200

# Obtener un producto por ID via API
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

# Obtener producto por ID
def get_producto(id):
    producto = Producto.query.get_or_404(id) # Obtener producto o 404
    return jsonify(producto.to_dict()), 200

# Actualizar un producto via API
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

# Actualizar producto
def update_producto(id):

    producto = Producto.query.get_or_404(id) # Obtener producto o 404
    
    # Verificar que el usuario sea el dueño o admin
    user = User.query.filter_by(username=request.user).first()
    if producto.user_id != user.id and request.role != 'admin':
        return jsonify({"error": "No tienes permiso para modificar este producto"}), 403
    
    try: # Validar y deserializar los datos de entrada
        data = producto_schema.load(request.json, partial=True)
    except ValidationError as err: # Si hay errores de validación, devolverlos
        return jsonify({"errors": err.messages}), 400
    
    # Actualizar campos
    if 'nombre' in data:
        producto.nombre = data['nombre']
    if 'descripcion' in data:
        producto.descripcion = data['descripcion']
    if 'precio' in data:
        producto.precio = data['precio']
    if 'stock' in data:
        producto.stock = data['stock']
    
    db.session.commit()
    
    return jsonify({
        "message": "Producto actualizado",
        "producto": producto.to_dict()
    }), 200

# Eliminar un producto via API
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

# Eliminar producto
def delete_producto(id):
    
    producto = Producto.query.get_or_404(id)
    
    # Verificar que el usuario sea el dueño o admin
    user = User.query.filter_by(username=request.user).first()
    if producto.user_id != user.id and request.role != 'admin': # Si no es dueño ni admin
        return jsonify({"error": "No tienes permiso para eliminar este producto"}), 403
    
    db.session.delete(producto)
    db.session.commit()
    
    return jsonify({"message": "Producto eliminado"}), 200

# Obtener productos de un usuario específico via API
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

# Obtener productos de un usuario específico via API
def get_productos_usuario(user_id):
    
    user = User.query.get_or_404(user_id) # Verificar que el usuario exista
    productos = Producto.query.filter_by(user_id=user_id).all() # Obtener productos del usuario
    result = productos_schema.dump(productos)
    
    return jsonify({
        "user": user.username,
        "productos": result,
        "total": len(result)
    }), 200