#!/bin/bash

echo "🛑 Deteniendo servicios..."

cd ~/proyecto

# Detener NGINX
if sudo nginx -s quit 2>/dev/null; then
    echo "✅ NGINX detenido"
else
    echo "⚠️  NGINX ya estaba detenido"
fi

# Detener Gunicorn
if [ -f "logs/gunicorn.pid" ]; then
    PID=$(cat logs/gunicorn.pid)
    if kill $PID 2>/dev/null; then
        echo "✅ Gunicorn PID $PID detenido"
    else
        echo "⚠️  PID no válido, usando pkill..."
        pkill -f gunicorn
    fi
    rm logs/gunicorn.pid
else
    if pkill -f gunicorn 2>/dev/null; then
        echo "✅ Gunicorn detenido"
    else
        echo "⚠️  Gunicorn ya estaba detenido"
    fi
fi

# Verificar
echo "🔍 Verificando..."
PROCS=$(ps aux | grep -E "(nginx|gunicorn)" | grep -v grep | wc -l)
if [ $PROCS -eq 0 ]; then
    echo "✅ Todos los servicios detenidos"
else
    echo "⚠️  Algunos procesos siguen activos:"
    ps aux | grep -E "(nginx|gunicorn)" | grep -v grep
fi

echo "🏁 Detención completada"
