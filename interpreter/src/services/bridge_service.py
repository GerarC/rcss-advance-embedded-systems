import socket
import threading
import re
import time

class BridgeService:
    def __init__(self):
        self.esp32_ip = "0.0.0.0"
        self.esp32_port = 5000
        self.server_ip = "127.0.0.1"
        self.initial_server_port = 6000
        self.current_server_port = 6000
        
        self.esp_socket = None
        self.esp_conn = None
        self.esp_addr = None
        self.server_socket = None
        
        self.running = False
        self.threads = []
        self.bandera = 1

    def start(self):
        if self.running:
            return {"status": "error", "message": "Bridge is already running"}

        try:
            # 1. TCP Connection with ESP32
            self.esp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.esp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.esp_socket.bind((self.esp32_ip, self.esp32_port))
            self.esp_socket.listen(1)
            
            # 2. UDP Socket for RoboCup
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.current_server_port = self.initial_server_port

            self.running = True
            
            # Start threads
            t_esp = threading.Thread(target=self._accept_esp32, daemon=True)
            t_server = threading.Thread(target=self._receive_from_server, daemon=True)
            
            self.threads = [t_esp, t_server]
            t_esp.start()
            t_server.start()
            
            return {"status": "success", "message": "Bridge service started. Waiting for ESP32..."}

        except Exception as e:
            self.stop()
            return {"status": "error", "message": str(e)}

    def stop(self):
        self.running = False
        
        if self.esp_conn:
            try:
                self.esp_conn.close()
            except:
                pass
            self.esp_conn = None

        if self.esp_socket:
            try:
                self.esp_socket.close()
            except:
                pass
            self.esp_socket = None
            
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
            
        return {"status": "success", "message": "Bridge service stopped"}

    def get_status(self):
        return {
            "running": self.running,
            "esp32_connected": self.esp_conn is not None,
            "esp32_addr": str(self.esp_addr) if self.esp_addr else None,
            "server_port": self.current_server_port
        }

    def send_command(self, command):
        if not self.server_socket:
            return {"status": "error", "message": "Bridge not running"}
            
        try:
            self.server_socket.sendto(command.encode(), (self.server_ip, self.current_server_port))
            return {"status": "success", "message": f"Sent: {command}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _accept_esp32(self):
        print("[INT] Waiting for ESP32 on port 5000...")
        try:
            while self.running:
                # Use timeout to allow checking self.running periodically if no connection
                self.esp_socket.settimeout(1.0) 
                try:
                    conn, addr = self.esp_socket.accept()
                    self.esp_conn = conn
                    self.esp_addr = addr
                    print("[INT] ESP32 connected from:", addr)
                    
                    # Handle this connection in a loop or separate thread? 
                    # For simplicity, let's handle receiving here since we only expect one ESP32
                    self._receive_from_esp32()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"[INT] Error accepting connection: {e}")
                    break
        except Exception as e:
            print(f"[INT] Accept loop error: {e}")

    def _receive_from_esp32(self):
        if not self.esp_conn:
            return

        try:
            while self.running and self.esp_conn:
                data = self.esp_conn.recv(1024)
                if not data:
                    print("[INT] ESP32 disconnected.")
                    break

                msg = data.decode()
                print("[ESP32]", msg)
                self._process_esp32_message(msg)
        except Exception as e:
            print(f"[INT] Error receiving from ESP32: {e}")
        finally:
            self.esp_conn = None
            self.esp_addr = None

    def _process_esp32_message(self, msg):
        msg = msg.strip()
        if msg.lower() == "init":
            print("[INT] INIT received -> sending (init MyTeam) to port 6000")
            texto = "(init MyTeam (version 15))"
            self.server_socket.sendto(texto.encode(), (self.server_ip, self.initial_server_port))
            return

        print(f"[INT] Forwarding to RoboCup server (UDP:{self.current_server_port}): {msg}")
        msg = "(" + msg + ")"
        self.server_socket.sendto(msg.encode(), (self.server_ip, self.current_server_port))

    def _receive_from_server(self):
        print("[INT] Listening for RoboCup server messages...")
        try:
            while self.running:
                if not self.server_socket:
                    time.sleep(0.1)
                    continue
                    
                # Non-blocking or timeout to check self.running
                self.server_socket.settimeout(1.0)
                try:
                    data, addr = self.server_socket.recvfrom(2048)
                    msg = data.decode().strip()
                    port_origin = addr[1]

                    # Update port if changed (after init)
                    if port_origin != self.current_server_port:
                        print(f"[INT] New port assigned by server: {port_origin}")
                        self.current_server_port = port_origin

                    # Process and forward to ESP32
                    self._process_server_message(msg, port_origin)
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"[INT] Error receiving from server: {e}")
        except Exception as e:
            print(f"[INT] Server receive loop error: {e}")

    def _process_server_message(self, msg, port_origin):
        if not self.esp_conn:
            return

        # Referee messages
        referee = re.findall(r"\(hear\s+\d+\s+referee\s+([a-zA-Z0-9_]+)\)", msg)
        for event in referee:
            texto = f"referee {event}\n"
            try:
                self.esp_conn.sendall(texto.encode())
                print("[INT -> ESP] referee event:", texto.strip())
            except Exception as e:
                print("[INT] Error sending referee to ESP:", e)

        # Vision messages (see)
        if msg.startswith("(see"):
            if self.bandera == 1:
                try:
                    self.esp_conn.sendall((msg + "\n").encode())
                    self.bandera = 0
                except:
                    pass
            else:
                # print(f"[SERVER:{port_origin}] {msg}")
                balls = re.findall(r"\(\(b\)\s*([\-0-9\.]+)\s*([\-0-9\.]+)\s*([\-0-9\.]+)\s*([\-0-9\.]+)\)", msg)
                
                # If no ball found? The original code logic was a bit weird here:
                # if balls == "": ... (this is never true for re.findall result which is a list)
                # But let's keep the logic of parsing balls if present.
                
                for dist, direction, nada, nada1 in balls:
                    texto = f"ball {dist} {direction} {nada} {nada1}\n"
                    try:
                        self.esp_conn.sendall(texto.encode())
                        print("[INT -> ESP] ball:", texto.strip())
                    except Exception as e:
                        print("[INT] Error sending ball to ESP:", e)
