# ----- Archivo de prueba para visualizar y decodificar un JWT -----

import jwt

# Para probar se pega la cookie token del navegador en /seguro
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoibWl1c3VhcmlvIiwicm9sZSI6ImFkbWluIiwiaWF0IjoxNzYwMzgxNTc2LCJleHAiOjE3NjAzODUxNzZ9.UyRQ0XP-C1l8_Fz8Di6qOopvYYfGB27SxukNC_siidM"

# Decodificar el token
payload = jwt.decode(token, "jwt_secret_key_local", algorithms=["HS256"])

print(payload)
