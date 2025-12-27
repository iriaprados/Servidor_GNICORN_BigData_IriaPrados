# ------ Rutas principales de la aplicación -----

from flask import render_template
from . import bp
from .controllers import MainController
from app.utils import token_requerido, admin_requerido

@bp.route("/", methods=["GET"])
def root():
    return MainController.index()

@bp.route("/inseguro")
def inseguro():
    return MainController.inseguro()

@bp.route("/seguro")
@token_requerido
def seguro():
    return MainController.seguro()

@bp.route("/api/usuario/protegido", methods=["GET"])
@token_requerido
def usuario_protegido():
    return MainController.usuario_protegido()

@bp.route("/api/usuario/listar", methods=["GET"])
@admin_requerido
def listar_usuarios():
    return MainController.listar_usuarios()

@bp.route('/usuarios/panel')
def panel_usuarios():
    return render_template('usuarios.html')