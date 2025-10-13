# Archivo para ver los datos del JWT
import jwt

# Para probar se pega la cookie token del navegador en /seguro
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoibWl1c3VhcmlvIiwicm9sZSI6ImFkbWluIiwiaWF0IjoxNzYwMzgxMTAwLCJleHAiOjE3NjAzODQ3MDB9.rQvt0qBs_Y7LE57pu8MKOoXcAnAOt6ATGIQsid_YG2I"

# Decodificar el token
payload = jwt.decode(token, "jwt_secret_key_local", algorithms=["HS256"])

print(payload)
