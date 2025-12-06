# ------- Esquemas de validación y serialización -------

from marshmallow import Schema, fields, validate

# Esquema para los usuarios
class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=False, allow_none=True)
    password = fields.Str(required=True, load_only=True, validate=validate.Length(min=4))
    role = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

# Esquema para las actualizaciones de usuario
class UserUpdateSchema(Schema):
    username = fields.Str(validate=validate.Length(min=3, max=80))
    email = fields.Email(allow_none=True)
    password = fields.Str(load_only=True, validate=validate.Length(min=4))

# Esquema para los productos
class ProductoSchema(Schema):
    """Schema para validar datos de producto"""
    id = fields.Int(dump_only=True)
    nombre = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    descripcion = fields.Str(allow_none=True)
    precio = fields.Float(required=True, validate=validate.Range(min=0))
    stock = fields.Int(validate=validate.Range(min=0))
    user_id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

# Instancias de schemas
user_schema = UserSchema()
users_schema = UserSchema(many=True)
user_update_schema = UserUpdateSchema()
producto_schema = ProductoSchema()
productos_schema = ProductoSchema(many=True)