# Inicializar las rutas del blueprint de productos

from flask import Blueprint

# Crear el blueprint
bp = Blueprint('productos', __name__)

# Importar las rutas (esto registra automáticamente todas las rutas)
from . import routes