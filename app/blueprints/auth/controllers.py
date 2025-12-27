# ------ Controlador de autenticación del usuario -----

from flask import render_template, request, redirect, url_for, make_response, session, current_app
from app.models import db, User
from app.utils import generar_jwt

class AuthController:

    # Registro de usuarios
    @staticmethod
    def register():
        
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            email = request.form.get("email")
            
            if not username or not password:
                return render_template("register.html", error="Faltan datos")
            
            if User.query.filter_by(username=username).first():
                return render_template("register.html", error="El usuario ya existe")
            
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            return render_template("register.html", success="Usuario creado correctamente")
        
        return render_template("register.html")
    
    # Login de usuarios
    @staticmethod
    def login():
        
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                token = generar_jwt(
                    user.username,
                    user.role,
                    current_app.config['JWT_SECRET'],
                    current_app.config['JWT_ALGORITHM'],
                    current_app.config['JWT_EXPIRATION_HOURS']
                )
                respuesta = redirect(url_for('main.seguro'))
                respuesta.set_cookie("token", token, httponly=True, 
                                   secure=current_app.config['IS_PRODUCTION'], 
                                   samesite='Lax')
                return respuesta
            
            return render_template("login.html", error="Usuario o contraseña incorrectos")
        
        return render_template("login.html")
    
    # Logout de usuarios
    @staticmethod
    def logout():
        
        user = session.get("user", "Usuario")
        session.clear()
        response = make_response(render_template("logout.html", 
                                                message=f"Sesión de {user} cerrada correctamente"))
        response.set_cookie('token', '', expires=0)
        return response