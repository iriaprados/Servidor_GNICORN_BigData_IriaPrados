# ----- Controladores para la gestión de productos -----

from flask import request, jsonify
from marshmallow import ValidationError
from app.models import db, User, Producto
from app.schemas import producto_schema, productos_schema


class ProductoController:
    # Crear un nuevo producto
    @staticmethod
    def create_producto():
        
        try:
            # Validar y deserializar los datos de entrada
            data = producto_schema.load(request.json)
        except ValidationError as err:
            # Si hay errores de validación, devolverlos
            return jsonify({"errors": err.messages}), 400
        
        # Obtener el usuario actual (viene del decorador @token_requerido)
        user = User.query.filter_by(username=request.user).first()
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        # Crear el producto
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
    
    # Listar todos los productos
    @staticmethod
    def get_productos():
        
        productos = Producto.query.all()
        result = productos_schema.dump(productos)
        return jsonify(result), 200
    
    # Obtener un producto por id
    @staticmethod
    def get_producto(id):
     
        producto = Producto.query.get_or_404(id)
        return jsonify(producto.to_dict()), 200
    
    # Actualizar un producto por id
    @staticmethod
    def update_producto(id):
        
        producto = Producto.query.get_or_404(id)
        
        # Verificar que el usuario sea el dueño o admin
        user = User.query.filter_by(username=request.user).first()
        if producto.user_id != user.id and request.role != 'admin':
            return jsonify({
                "error": "No tienes permiso para modificar este producto"
            }), 403
        
        try:
            # Validar datos (partial=True permite actualización parcial)
            data = producto_schema.load(request.json, partial=True)
        except ValidationError as err:
            return jsonify({"errors": err.messages}), 400
        
        # Actualizar solo los campos proporcionados
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
    
    # Eliminar un producto por id 
    @staticmethod
    def delete_producto(id):
     
        producto = Producto.query.get_or_404(id)
        
        # Verificar que el usuario sea el dueño o admin
        user = User.query.filter_by(username=request.user).first()
        if producto.user_id != user.id and request.role != 'admin':
            return jsonify({
                "error": "No tienes permiso para eliminar este producto"
            }), 403
        
        db.session.delete(producto)
        db.session.commit()
        
        return jsonify({"message": "Producto eliminado"}), 200
    
    # PRODUCTOS POR USUARIO
    @staticmethod
    def get_productos_usuario(user_id):
      
        # Verificar que el usuario existe
        user = User.query.get_or_404(user_id)
        
        # Obtener productos del usuario
        productos = Producto.query.filter_by(user_id=user_id).all()
        result = productos_schema.dump(productos)
        
        return jsonify({
            "user": user.username,
            "productos": result,
            "total": len(result)
        }), 200
