import socket
import time
import re

SERVER_IP = "127.0.0.1"
SERVER_PORT = 6000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(2.0)

# ============================
#  ENVIAR UNA ACCIÓN POR CICLO
# ============================
CICLO = 0.1   # 100 ms

def enviar(cmd):
    """Envía un comando y espera el ciclo para no 'sobrecomandar'."""
    sock.sendto(cmd.encode(), (SERVER_IP, server_port))
    time.sleep(CICLO)


# ============================
#   PARSEADOR
# ============================

def obtener_objeto(msg, nombre):
    patron = r"\(\(" + nombre + r"\)\s+([-\d.]+)\s+([-\d.]+)"
    m = re.search(patron, msg)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None


# ============================
#   CONEXIÓN AL SERVER
# ============================

sock.sendto(b"(init MyTeam (version 15))", (SERVER_IP, SERVER_PORT))
print(">> init enviado")

data, addr = sock.recvfrom(8192)
server_port = addr[1]
print("Servidor escuchando en puerto:", server_port)

enviar("(move -0.3 0)")    # posición inicial


# ============================
#   VARIABLES
# ============================

estado = "esperar_inicio"
info_balon = None
info_flag = None
OBJETIVO = "f p r c"
MAX_TURN = 15

dist_obj_anterior = None


# ============================
#   LOOP PRINCIPAL
# ============================

print("\n✅ Agente listo...\n")

while True:
    try:
        msg = sock.recvfrom(8192)[0].decode(errors="ignore").strip()

        # ===========================================
        # SOLO USAMOS VISIÓN "(see ...)" + referee
        # ===========================================

        # avanzar hacia el objetivo
        enviar(f"(kick 50 -45)")

        continue


    except socket.timeout:
        continue
    except KeyboardInterrupt:
        print("\nCliente detenido.\n")
        break

