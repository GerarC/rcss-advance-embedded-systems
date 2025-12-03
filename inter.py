import socket
import threading
import re

ESP32_IP = "0.0.0.0"
ESP32_PORT = 5000

SERVER_IP = "127.0.0.1"
SERVER_PORT = 6000  # SOLO PARA EL INIT
bandera = 1


# ============================================
# 1. Conexión TCP con ESP32
# ============================================
esp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
esp_socket.bind((ESP32_IP, ESP32_PORT))
esp_socket.listen(1)

print("[INT] Esperando ESP32 en puerto 5000...")
esp_conn, esp_addr = esp_socket.accept()
print("[INT] ESP32 conectado desde:", esp_addr)


# ============================================
# 2. Socket UDP hacia RoboCup
# ============================================
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Puerto actual del servidor (inicia en 6000)
current_server_port = SERVER_PORT


# ============================================
# Procesar comandos desde el ESP32
# ============================================
def procesar_mensaje_esp32(msg):
    global current_server_port
    msg = msg.strip()

    if msg.lower() == "init":
        print("[INT] INIT recibido → enviando (init MyTeam) al puerto 6000")
        texto = "(init MyTeam (version 15))"
        server_socket.sendto(texto.encode(), (SERVER_IP, SERVER_PORT))
        return

    print(f"[INT] Reenviando a server RoboCup (UDP:{current_server_port}): {msg}")
    msg = "("+msg+")"
    server_socket.sendto(msg.encode(), (SERVER_IP, current_server_port))


# ============================================
# Recibir mensajes del ESP32
# ============================================
def recibir_de_esp32():
    while True:
        data = esp_conn.recv(1024)
        if not data:
            print("[INT] ESP32 desconectado.")
            break

        msg = data.decode()
        print("[ESP32]", msg)
        procesar_mensaje_esp32(msg)


# ============================================
# Recibir mensajes del servidor
# ============================================
def recibir_del_server():
    global current_server_port
    global bandera
    
    while True:
        data, addr = server_socket.recvfrom(2048)
        msg = data.decode().strip()
        puerto_origen = addr[1]


        # ------------------------------
        # Detectar si el servidor cambió de puerto
        # RoboCup cambia el puerto DESPUÉS del init
        # ------------------------------
        if puerto_origen != current_server_port:
            print(f"[INT] Nuevo puerto asignado por el servidor: {puerto_origen}")
            current_server_port = puerto_origen
        #print(f"[SERVER:{puerto_origen}] {msg}")
        # Reenviar al ESP32
        referee = re.findall(r"\(hear\s+\d+\s+referee\s+([a-zA-Z0-9_]+)\)", msg)
        for event in referee:
            texto = f"referee {event}\n"
            try:
                esp_conn.sendall(texto.encode())
                print("[INT → ESP] referee event:", texto.strip())
            except Exception as e:
                print("[INT] Error enviando referee al ESP:", e)
                
        if msg.startswith("(see"):
            if bandera == 1:
                esp_conn.sendall((msg + "\n").encode())
                bandera = 0
            else:
                print(f"[SERVER:{puerto_origen}] {msg}")
                balls = re.findall(r"\(\(b\)\s*([\-0-9\.]+)\s*([\-0-9\.]+)\s*([\-0-9\.]+)\s*([\-0-9\.]+)\)", msg)
                if balls == "":
                    dist = -1
                    direction = -1
                    nada = -1
                    nada1 = -1
                    texto = f"ball {dist} {direction} {nada} {nada1}\n"
                    esp_conn.sendall(texto.encode())
                for dist, direction, nada, nada1 in balls:
                    texto = f"ball {dist} {direction} {nada} {nada1}\n"
                    esp_conn.sendall(texto.encode())
                    print("[INT → ESP] balón:", texto.strip())
            #esp_conn.sendall((msg + "\n").encode())


# ============================================
# Hilos de comunicación
# ============================================
threading.Thread(target=recibir_de_esp32, daemon=True).start()
threading.Thread(target=recibir_del_server, daemon=True).start()


# ============================================
# Consola manual para enviar comandos al servidor
# ============================================
while True:
    texto = input("> ")
    server_socket.sendto(texto.encode(), (SERVER_IP, current_server_port))
