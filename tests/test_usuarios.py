#  ------ Pruebas unitarias para endpoints de usuarios -------

import pytest
import json
from app import create_app, db
from app.models import User

# Fixture para crear la aplicación de prueba
@pytest.fixture
def app():

    app = create_app('default')
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

# Fixture para el cliente de prueba
@pytest.fixture
def client(app):
    """Cliente de testing"""
    return app.test_client()

# Fixture para headers de autenticación
@pytest.fixture
def auth_headers(client):

    # Crear usuario de prueba
    user = User(username="testuser", email="test@test.com", role="user")
    user.set_password("testpass")
    db.session.add(user)
    db.session.commit()
    
    # Hacer login
    response = client.post('/api/usuarios/login',
                          data=json.dumps({
                              'username': 'testuser',
                              'password': 'testpass'
                          }),
                          content_type='application/json')
    
    token = response.json['access_token']
    return {'Authorization': f'Bearer {token}'}

# Fixture para headers de autenticación de admin
@pytest.fixture
def admin_headers(client):

    # Crear usuario admin
    admin = User(username="admin", email="admin@test.com", role="admin")
    admin.set_password("adminpass")
    db.session.add(admin)
    db.session.commit()
    
    # Hacer login
    response = client.post('/api/usuarios/login',
                          data=json.dumps({
                              'username': 'admin',
                              'password': 'adminpass'
                          }),
                          content_type='application/json')
    
    token = response.json['access_token']
    return {'Authorization': f'Bearer {token}'}

# Test para el registro de un nuevo usuario
def test_register_usuario(client):
    response = client.post('/api/usuarios/register',
                          data=json.dumps({
                              'username': 'newuser',
                              'email': 'new@test.com',
                              'password': 'password123'
                          }),
                          content_type='application/json')
    
    assert response.status_code == 201
    assert 'user' in response.json
    assert response.json['user']['username'] == 'newuser'

# Test para el registro de un usuario duplicado
def test_register_usuario_duplicado(client):

    # Primer registro
    client.post('/api/usuarios/register',
               data=json.dumps({
                   'username': 'duplicado',
                   'password': 'pass123'
               }),
               content_type='application/json')
    
    # Segundo registro (debe fallar)
    response = client.post('/api/usuarios/register',
                          data=json.dumps({
                              'username': 'duplicado',
                              'password': 'pass456'
                          }),
                          content_type='application/json')
    
    assert response.status_code == 400
    assert 'error' in response.json

# Test para login exitoso
def test_login_exitoso(client):

    # Crear usuario
    user = User(username="logintest", email="login@test.com")
    user.set_password("correctpass")
    db.session.add(user)
    db.session.commit()
    
    # Intentar login
    response = client.post('/api/usuarios/login',
                          data=json.dumps({
                              'username': 'logintest',
                              'password': 'correctpass'
                          }),
                          content_type='application/json')
    
    assert response.status_code == 200
    assert 'access_token' in response.json
    assert 'user' in response.json

# Test para login fallido
def test_login_fallido(client):
    response = client.post('/api/usuarios/login',
                          data=json.dumps({
                              'username': 'noexiste',
                              'password': 'wrongpass'
                          }),
                          content_type='application/json')
    
    assert response.status_code == 401
    assert 'error' in response.json

# Test para acceder a ruta privada sin token
def test_acceso_privado_sin_token(client):
    response = client.get('/api/usuarios/privado')
    assert response.status_code == 401

# Test para acceder a ruta privada con token
def test_acceso_privado_con_token(client, auth_headers):
    response = client.get('/api/usuarios/privado', headers=auth_headers)
    assert response.status_code == 200
    assert response.json['msg'] == 'Acceso autorizado'

# Test para listar usuarios sin permisos
def test_listar_usuarios_sin_permisos(client, auth_headers):
    response = client.get('/api/usuarios', headers=auth_headers)
    assert response.status_code == 403

# Test para listar usuarios con permisos de admin
def test_listar_usuarios_admin(client, admin_headers):
    response = client.get('/api/usuarios', headers=admin_headers)
    assert response.status_code == 200
    assert isinstance(response.json, list)

# Test para obtener un usuario específico por ID
def test_obtener_usuario_por_id(client, auth_headers):
    # Crear usuario
    user = User(username="getuser", email="get@test.com")
    user.set_password("pass123")
    db.session.add(user)
    db.session.commit()
    
    response = client.get(f'/api/usuarios/{user.id}', headers=auth_headers)
    assert response.status_code == 200
    assert response.json['username'] == 'getuser'

# Test para que un usuario pueda actualizar sus propios datos
def test_actualizar_usuario_propio(client, auth_headers):
    # Obtener el ID del usuario testuser
    user = User.query.filter_by(username='testuser').first()
    
    response = client.put(f'/api/usuarios/{user.id}',
                         headers=auth_headers,
                         data=json.dumps({
                             'email': 'newemail@test.com'
                         }),
                         content_type='application/json')
    
    assert response.status_code == 200
    assert response.json['user']['email'] == 'newemail@test.com'

# Test para que un admin pueda eliminar usuarios
def test_eliminar_usuario_admin(client, admin_headers):
    # Crear usuario a eliminar
    user = User(username="todelete", email="delete@test.com")
    user.set_password("pass123")
    db.session.add(user)
    db.session.commit()
    
    response = client.delete(f'/api/usuarios/{user.id}', headers=admin_headers)
    assert response.status_code == 200
    
    # Verificar que fue eliminado
    deleted_user = User.query.get(user.id)
    assert deleted_user is None
