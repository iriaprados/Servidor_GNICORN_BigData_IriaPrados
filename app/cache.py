# ------- Sistema de caché con Redis (Anexo A.2) -------

import json
from functools import wraps
from flask import request, jsonify
from datetime import datetime

# Clase para gestionar el sistema de write-through cache
class CacheManager:

    # Inicializar con cliente Redis
    def __init__(self, redis_client):
        self.redis = redis_client
        self.stats = {
            'hits': 0,
            'misses': 0,
            'writes': 0,
            'invalidations': 0
        }
    
    # Leer los valores de caché
    def get(self, key):

        if not self.redis: # En el caso que no haya conexión a Redis
            return None
        
        try: 
            value = self.redis.get(key) # Intentar obtener el valor

            if value: # Si hay valores 
                self.stats['hits'] += 1
                print(f" Cache HIT: {key}")
                return json.loads(value)
            else: # Si no hay valores en la caché 
                self.stats['misses'] += 1 # Contar miss
                print(f" Cache MISS: {key}")
                return None
            
        except Exception as e: # Manejo de errores en la lectura de caché
            print(f"Error leyendo caché: {e}")
            return None
    
    # Función para escribir en caché
    def set(self, key, value, ttl=300):
     
        if not self.redis: # En el caso que no haya conexión a Redis se sale
            return False
        
        try: 
            self.redis.setex(key, ttl, json.dumps(value)) # Guardar valor con TTL
            self.stats['writes'] += 1 # Contar escritura
            print(f"Cache WRITE: {key} (TTL: {ttl}s)") # Indicar escritura
            return True
         
        except Exception as e: # Manejo de errores en la escritura de caché
            print(f"Error escribiendo en caché: {e}")
            return False
        
    # Función para eliminar una clave de caché
    def delete(self, key):

        if not self.redis:
            return False
        
        try:
            deleted = self.redis.delete(key) # Eliminar clave

            if deleted: # Si se eliminó
                self.stats['invalidations'] += 1 # Contar invalidación
                print(f"Cache INVALIDATED: {key}")
            return deleted > 0
        
        except Exception as e: # Manejo de errores en la invalidación de caché
            print(f"Error invalidando caché: {e}")
            return False
    
    # Función para eliminar múltiples claves por patrón
    def delete_pattern(self, pattern):
    
        if not self.redis: # En el caso que no haya conexión a Redis se sale
            return 0
        
        try:

            keys = self.redis.keys(pattern) # Buscar claves por patrón

            if keys: # Si hay claves que eliminar
                deleted = self.redis.delete(*keys) # Eliminar claves
                self.stats['invalidations'] += deleted # Contar invalidaciones
                print(f" Cache INVALIDATED: {deleted} claves ({pattern})")
                return deleted
            return 0
        
        except Exception as e: # Manejo de errores en la invalidación por patrón
            print(f"Error invalidando patrón: {e}")
            return 0
    
    # Función para obtener estadísticas de caché
    def get_stats(self):

        total_requests = self.stats['hits'] + self.stats['misses'] # Total de solicitudes
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0 # Tasa de aciertos
        
        # Estadísticas de Redis
        redis_info = {}
        if self.redis:

            try:
                info = self.redis.info('stats') # Obtener información de estadísticas de Redis
                # Información de Redis
                redis_info = {
                    'total_commands': info.get('total_commands_processed', 0),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0),
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory_human': self.redis.info('memory').get('used_memory_human', 'N/A')
                }
            except:
                pass
        
        return { # Devolver estadísticas de la aplicación y de Redis
            'application_stats': {
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'writes': self.stats['writes'],
                'invalidations': self.stats['invalidations'],
                'hit_rate': round(hit_rate, 2),
                'total_requests': total_requests
            },
            'redis_stats': redis_info,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    # Función para limpiar toda la caché
    def clear_all(self):

        if not self.redis:
            return False
        
        try:
            self.redis.flushdb() # Limpiar toda la base de datos de Redis
            print("Toda la caché fue limpiada")
            return True
        
        except Exception as e: # Manejo de errores al limpiar la caché
            print(f" Error limpiando caché: {e}")
            return False

# Decorador para cachear resultados de endpoints
def cache_result(key_prefix, ttl=300):
   
    def decorator(f):
        @wraps(f)

        # Decorador que maneja la caché
        def wrapper(*args, **kwargs):
            from app import redis_client # Importar el cliente Redis
            
            if not redis_client: # Si no hay conexión a Redis, ejecutar función directamente
                return f(*args, **kwargs)
            
            # Construir clave única
            cache_key = f"{key_prefix}:{request.path}:{request.query_string.decode()}"
            
            # Intentar obtener de caché (READ)
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    print(f"Cache HIT: {cache_key}")
                    data = json.loads(cached)
                    return jsonify(data), 200
                
            except Exception as e:
                print(f"Error leyendo caché: {e}")
            
            # Cache MISS: ejecutar función
            print(f"Cache MISS: {cache_key}")
            result = f(*args, **kwargs)
            
            # Guardar en caché (WRITE-THROUGH)
            try:
                if isinstance(result, tuple):
                    data, status = result
                else:
                    data, status = result, 200
                
                # Extraer JSON del objeto Response si es necesario
                if hasattr(data, 'get_json'):
                    json_data = data.get_json()
                elif isinstance(data, dict):
                    json_data = data
                else:
                    json_data = data
                
                redis_client.setex(cache_key, ttl, json.dumps(json_data))
                print(f"Guardado en caché: {cache_key} (TTL: {ttl}s)")
                
                return jsonify(json_data), status
            except Exception as e:
                print(f"Error guardando en caché: {e}")
                return result
        
        return wrapper
    return decorator

# Función para invalidar caché por patrón
def invalidate_cache(pattern):
   
    from app import redis_client # Importar el cliente Redis
    
    if not redis_client: # Si no hay conexión a Redis, salir
        return 0
    
    try:
        keys = redis_client.keys(pattern) # Buscar claves por patrón

        if keys: # Si hay claves que eliminar
            deleted = redis_client.delete(*keys) # Eliminar claves
            print(f"Cache invalidado: {deleted} claves ({pattern})") 
            return deleted
        return 0
    
    except Exception as e: # Manejo de errores en la invalidación de caché
        print(f"Error invalidando caché: {e}")
        return 0