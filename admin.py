# Script para definir un usuario admin en la base de datos
import sqlite3
from werkzeug.security import generate_password_hash

DB = "users.db"
username = "miusuario" # Nombre de tu usuario admin
password = "1234" # Cambia esto por la contraseña que quieras

# Crear el hash seguro de la contraseña
password_hash = generate_password_hash(password)

# Conexión a la base de datos
conn = sqlite3.connect(DB)
cur = conn.cursor()

# Comprobamos si el usuario ya existe
cur.execute("SELECT id FROM users WHERE username=?", (username,))
row = cur.fetchone()

if row:
    # Si existe, actualizamos su contraseña y rol
    cur.execute("UPDATE users SET password_hash=?, role='admin' WHERE username=?", (password_hash, username))
    print(f"Usuario '{username}' actualizado como admin con nueva contraseña.")
else:
    # Si no existe, lo creamos como admin
    cur.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'admin')",
                (username, password_hash))
    print(f"Usuario '{username}' creado como admin con contraseña establecida.")

conn.commit()
conn.close()

print("Contraseña guardada correctamente. Puedes iniciar sesión con:")
print(f"Usuario: {username}")
print(f"Contraseña: {password}")
