# ------- Rutas relacionadas con productos -------
from flask import Blueprint, request, jsonify, current_app
from marshmallow import ValidationError
from app.models import db, User, Producto
from app.schemas import producto_schema, productos_schema
from app.utils import token_requerido, admin_requerido

bp = Blueprint('productos', __name__)

# Crear un nuevo producto via API
@bp.route('/productos', methods=['POST'])
@token_requerido

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

def get_productos():
    productos = Producto.query.all() # Obtener todos los productos
    result = productos_schema.dump(productos) # Serializar los productos
    return jsonify(result), 200

# Obtener un producto por ID via API
@bp.route('/productos/<int:id>', methods=['GET'])

def get_producto(id):
    producto = Producto.query.get_or_404(id) # Obtener producto o 404
    return jsonify(producto.to_dict()), 200

# Actualizar un producto via API
@bp.route('/productos/<int:id>', methods=['PUT'])
@token_requerido

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
def get_productos_usuario(user_id):
    
    user = User.query.get_or_404(user_id) # Verificar que el usuario exista
    productos = Producto.query.filter_by(user_id=user_id).all() # Obtener productos del usuario
    result = productos_schema.dump(productos)
    
    return jsonify({
        "user": user.username,
        "productos": result,
        "total": len(result)
    }), 200