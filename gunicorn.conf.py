import multiprocessing
import os

# Configuración del servidor
bind = "127.0.0.1:8000"  # Solo escucha en localhost, NGINX será el proxy
backlog = 2048

# Procesos worker
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 5
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Seguridad
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Nombrado del proceso
proc_name = "flask_cookies_app"

# Configuración avanzada
preload_app = True
daemon = False
pidfile = "logs/gunicorn.pid"
user = None
group = None

# Variables de entorno para Flask
raw_env = [
    "FLASK_ENV=production",
    "SECRET_KEY=tu_clave_secreta_super_segura_aqui"
]