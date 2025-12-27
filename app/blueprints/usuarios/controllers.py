# ---- Controlador de usuarios ----

from flask import request, jsonify, current_app
from marshmallow import ValidationError
from app.models import db, User
from app.schemas import user_schema, users_schema, user_update_schema
from app.utils import generar_jwt
from app.cache import invalidate_cache
import json


class UsuarioController:

    
    @staticmethod
    def register():
        try: # Validar datos de entrada
            data = user_schema.load(request.json)

        except ValidationError as err: # Manejar errores de validación
            return jsonify({"errors": err.messages}), 400
        
        # Verificar si el usuario ya existe
        if User.query.filter_by(username=data['username']).first():
            return jsonify({"error": "El usuario ya existe"}), 400
        
        # Crear nuevo usuario
        user = User(username=data['username'], email=data.get('email'))
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            "message": "Usuario creado", 
            "user": user.to_dict()
        }), 201
    
    # Login de usuarios
    @staticmethod
    def login():
        
        data = request.json # Obtener datos de la solicitud
        if not data: # Validar datos
            return jsonify({"error": "No se enviaron datos"}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password: # Validar campos requeridos
            return jsonify({"error": "Faltan campos requeridos"}), 400
        
        # Buscar usuario
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return jsonify({"error": "Credenciales inválidas"}), 401
        
        # Generar token JWT
        token = generar_jwt(
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
    
    # Listar todos los usuarios (requiere admin)
    @staticmethod
    def get_usuarios():
      
        from app import redis_client
        cache_key = "usuarios:all"
        
        # Intentar obtener de caché
        if redis_client:
            try: # Leer desde Redis
                cached = redis_client.get(cache_key)

                if cached:
                    print("✅ Datos obtenidos desde caché Redis")
                    return jsonify(json.loads(cached)), 200
                
            except Exception as e: # Manejar errores de Redis
                print(f"Error al leer de Redis: {e}")
        
        # Si no hay caché, consultar BD
        users = User.query.all()
        result = users_schema.dump(users)
        
        # Guardar en caché por 5 minutos
        if redis_client:
            try:
                redis_client.setex(cache_key, 300, json.dumps(result))
                print("✅ Datos guardados en caché Redis")
            except Exception as e: # Manejar errores de Redis
                print(f"Error al escribir en Redis: {e}")
        
        return jsonify(result), 200
    
    # Obtener usuario por ID
    @staticmethod
    def get_usuario(id):
       
        user = User.query.get_or_404(id) # Obtener usuario o 404
        return jsonify(user.to_dict()), 200
    
    # Actualizar usuario
    @staticmethod
    def update_usuario(id):
     
        user = User.query.get_or_404(id) 
        
        # Verificar permisos
        if request.role != 'admin' and request.user != user.username:
            return jsonify({"error": "No tienes permiso"}), 403
        
        try: # Validar datos de entrada
            data = user_update_schema.load(request.json, partial=True)

        except ValidationError as err: # Manejar errores de validación
            return jsonify({"errors": err.messages}), 400
        
        # Actualizar campos
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']
        if 'password' in data:
            user.set_password(data['password'])
        
        db.session.commit()
        
        # Invalidar caché (write-through)
        invalidate_cache("usuarios:*")
        print(f"✅ Usuario {id} actualizado, caché invalidado")
        
        return jsonify({
            "message": "Usuario actualizado", 
            "user": user.to_dict()
        }), 200
    
    # Eliminar usuario
    @staticmethod
    def delete_usuario(id):
      
        user = User.query.get_or_404(id)
        db.session.delete(user)
        db.session.commit()
        
        # Invalidar caché (write-through)
        invalidate_cache("usuarios:*")
        print(f"✅ Usuario {id} eliminado, caché invalidado")
        
        return jsonify({"message": "Usuario eliminado"}), 200
    
    # Endpoint privado de prueba
    @staticmethod
    def privado():
        
        return jsonify({
            "msg": "Acceso autorizado", 
            "user": request.user,
            "role": request.role
        }), 200
    
    # Estadísticas de caché
    @staticmethod
    def cache_stats():
      
        if hasattr(current_app, 'cache_manager'): # Verificar manager
            stats = current_app.cache_manager.get_stats() # Obtener estadísticas
            return jsonify(stats), 200
        else: # Manejar ausencia de manager
            return jsonify({"error": "Cache manager no disponible"}), 503
    
    # Limpiar caché
    @staticmethod
    def clear_cache():
        invalidate_cache("*")
        return jsonify({"message": "Caché completamente limpiado"}), 200