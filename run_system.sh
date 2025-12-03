#!/bin/bash

# Colores para los logs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Iniciando Sistema RoboCup ===${NC}"

# 1. Verificar y liberar puerto 6000
echo -e "${GREEN}[1/5] Verificando puerto 6000...${NC}"
if fuser -k 6000/udp > /dev/null 2>&1; then
    echo -e "${RED}    -> Proceso en puerto 6000 eliminado.${NC}"
else
    echo "    -> Puerto 6000 libre."
fi
sleep 1

# 2. Arrancar rcssserver
echo -e "${GREEN}[2/5] Iniciando rcssserver...${NC}"
# Ejecutamos en background y silenciamos salida para no ensuciar la terminal, o redirigimos a log
/home/andres/rcssserver/build/rcssserver > rcssserver.log 2>&1 &
SERVER_PID=$!
echo "    -> rcssserver iniciado (PID: $SERVER_PID)"
sleep 2 # Esperar a que el servidor esté listo

# 3. Ejecutar cliente.py
echo -e "${GREEN}[3/5] Iniciando cliente.py (Jugador 1)...${NC}"
# Asumimos que estamos en la raíz del proyecto
python3 cliente.py > cliente.log 2>&1 &
CLIENT_PID=$!
echo "    -> cliente.py iniciado (PID: $CLIENT_PID)"
sleep 2

# 4. Arrancar rcssmonitor
echo -e "${GREEN}[4/5] Iniciando rcssmonitor...${NC}"
/home/andres/rcssmonitor/build/rcssmonitor > /dev/null 2>&1 &
MONITOR_PID=$!
echo "    -> rcssmonitor iniciado (PID: $MONITOR_PID)"
sleep 2

# 5. Arrancar interpreter
echo -e "${GREEN}[5/5] Iniciando Interpreter (Bridge para ESP32)...${NC}"
cd interpreter
# Usamos exec para que el script de bash sea reemplazado por el proceso de python
# Esto permite que al cerrar con Ctrl+C se cierre el python
echo "    -> Ejecutando src.main..."
./.venv/bin/python3 -m src.main

# Nota: Los procesos en background (server, cliente, monitor) seguirán corriendo
# si cierras este script. Para cerrarlos podrías necesitar un 'pkill' o cerrarlos manualmente.
# Cierra todo lo que arrancaste
trap "kill $SERVER_PID $CLIENT_PID $MONITOR_PID 2>/dev/null" EXIT
