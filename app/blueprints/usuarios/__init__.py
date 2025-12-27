# app/blueprints/usuarios/__init__.py
from flask import Blueprint

bp = Blueprint('usuarios', __name__)

from . import routes