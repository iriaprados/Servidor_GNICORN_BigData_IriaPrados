# ------ Rutas principaless de autenticación ------

from flask import render_template, request, redirect, url_for, make_response
from . import bp
from .controllers import AuthController

@bp.route("/register", methods=["GET", "POST"])
def register():
    """Ruta de registro de usuarios"""
    return AuthController.register()

@bp.route("/login", methods=["POST", "GET"])
def login():
    """Ruta de login de usuarios"""
    return AuthController.login()

@bp.route("/logout", methods=["POST", "GET"])
def logout():
    """Ruta de logout de usuarios"""
    return AuthController.logout()