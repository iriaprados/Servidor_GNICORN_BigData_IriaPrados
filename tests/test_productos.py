# ------- Tests para rutas de productos -------

import pytest
import json
from app import create_app, db
from app.models import User, Producto

# Fixture para la aplicación de testing
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

# Fixture para el cliente de testing
@pytest.fixture

def client(app):
    return app.test_client()

# Fixture para headers de autenticación
@pytest.fixture

def auth_headers(client):

    user = User(username="testuser", email="test@test.com")
    user.set_password("testpass")
    db.session.add(user)
    db.session.commit()
    
    response = client.post('/api/usuarios/login',
                          data=json.dumps({
                              'username': 'testuser',
                              'password': 'testpass'
                          }),
                          content_type='application/json')
    
    token = response.json['access_token']
    return {'Authorization': f'Bearer {token}'}

# Test para crear un nuevo producto
def test_crear_producto(client, auth_headers):

    # Crear producto
    response = client.post('/api/productos',
                          headers=auth_headers,
                          data=json.dumps({
                              'nombre': 'Laptop',
                              'descripcion': 'Laptop de prueba',
                              'precio': 999.99,
                              'stock': 5
                          }),
                          content_type='application/json')
    
    assert response.status_code == 201
    assert response.json['producto']['nombre'] == 'Laptop'

# Test para listar todos los productos
def test_listar_productos(client):
    response = client.get('/api/productos')
    assert response.status_code == 200
    assert isinstance(response.json, list)

# Test para obtener un producto por ID
def test_obtener_producto_por_id(client, auth_headers):

    # Crear producto
    user = User.query.filter_by(username='testuser').first()
    producto = Producto(
        nombre='Test Product',
        precio=100.0,
        user_id=user.id
    )
    db.session.add(producto)
    db.session.commit()
    
    response = client.get(f'/api/productos/{producto.id}')
    assert response.status_code == 200
    assert response.json['nombre'] == 'Test Product'

# Test para actualizar un producto propio
def test_actualizar_producto(client, auth_headers):

    # Crear producto
    user = User.query.filter_by(username='testuser').first()
    producto = Producto(
        nombre='Original',
        precio=100.0,
        user_id=user.id
    )
    db.session.add(producto)
    db.session.commit()
    
    # Actualizar
    response = client.put(f'/api/productos/{producto.id}',
                         headers=auth_headers,
                         data=json.dumps({
                             'nombre': 'Actualizado',
                             'precio': 200.0
                         }),
                         content_type='application/json')
    
    assert response.status_code == 200
    assert response.json['producto']['nombre'] == 'Actualizado'

# Test para eliminar un producto propio
def test_eliminar_producto(client, auth_headers):

    # Crear producto
    user = User.query.filter_by(username='testuser').first()
    producto = Producto(
        nombre='To Delete',
        precio=50.0,
        user_id=user.id
    )
    db.session.add(producto)
    db.session.commit()
    
    # Eliminar
    response = client.delete(f'/api/productos/{producto.id}', headers=auth_headers)
    assert response.status_code == 200
    
    # Verificar eliminación
    deleted = Producto.query.get(producto.id)
    assert deleted is None

# Test para listar productos por usuario
def test_productos_por_usuario(client, auth_headers):
  
    user = User.query.filter_by(username='testuser').first()
    
    # Crear varios productos
    for i in range(3):
        producto = Producto(
            nombre=f'Producto {i}',
            precio=100.0 * i,
            user_id=user.id
        )
        db.session.add(producto)
    db.session.commit()
    
    response = client.get(f'/api/productos/usuario/{user.id}')
    assert response.status_code == 200
    assert response.json['total'] == 3