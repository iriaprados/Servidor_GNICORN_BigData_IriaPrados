# ---- Inicilación de los módulos de blueprints ----

from flask import Blueprint

bp = Blueprint('auth', __name__)

from . import routes