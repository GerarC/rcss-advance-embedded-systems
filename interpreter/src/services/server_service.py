# src/services/server_manager.py

import errno
import os
import signal
import socket
import subprocess
import time


class ServerManager:
    """Manages the lifecycle of the external rcssserver process."""

    def __init__(
        self,
        command: list[str] = [],
        host: str = "127.0.0.1",
        port: int = 6000,
    ):
        self.server_command: list[str] = command if len(command) else ["rcssserver"]
        self.server_host: str = host
        self.server_port: int = port
        self._server_process: subprocess.Popen[bytes]|None = None

    def _is_port_in_use(self, host: str = "127.0.0.1", port: int = 6000):
        """Checks if the TCP port is currently in use."""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind((host, port))
            return False  # Free
        except socket.error as e:
            if e.errno == errno.EADDRINUSE:
                return True  # In use
            else:
                print(f"Unexpected error when checking port {self.server_port}: {e}")
                return True
        finally:
            s.close()

    def get_status(self):
        """Returns the current status of the server."""

        if self._server_process and self._server_process.poll() is None:
            return {
                "status": "running",
                "pid": self._server_process.pid,
                "port": self.server_port,
            }
        else:
            # If the process terminated or doesn't exist, clear the reference
            self._server_process = None
            return {"status": "stopped", "port": self.server_port}

    def start_server(self):
        """Starts the server if the port is free and the server is not already running."""

        if self._is_port_in_use(self.server_host):
            return {
                "status": "failed",
                "message": f"Port {self.server_port} is already in use.",
            }

        current_status = self.get_status()
        if current_status["status"] == "running":
            return {"status": "failed", "message": "The server is already running."}

        try:
            self._server_process = subprocess.Popen(self.server_command, shell=False)

            time.sleep(0.5)

            return {
                "status": "success",
                "message": f"Server started with PID: {self._server_process.pid}",
            }

        except FileNotFoundError:
            return {
                "status": "failed",
                "message": "Error: The 'rcssserver' command was not found. Ensure it is in your PATH.",
            }
        except Exception as e:
            return {"status": "failed", "message": f"Error starting server: {e}"}

    def stop_server(self):
        """Stops the rcssserver process if it is currently running."""

        if self._server_process is None or self._server_process.poll() is not None:
            return {
                "status": "failed",
                "message": "The server is not running or was not started by this API instance.",
            }

        try:
            pid = self._server_process.pid
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)

            if self._server_process.poll() is None:
                os.kill(pid, signal.SIGKILL)

            self._server_process = None  # Clear the reference
            return {
                "status": "success",
                "message": f"Server (PID {pid}) stopped successfully.",
            }

        except ProcessLookupError:
            self._server_process = None
            return {
                "status": "failed",
                "message": "The server process had already terminated.",
            }
        except Exception as e:
            return {"status": "failed", "message": f"Error stopping server: {e}"}

    def restart_server(self):
        """Stops the server and starts it again."""

        stop_result = self.stop_server()

        if stop_result["status"] == "success":
            time.sleep(1)

        start_result = self.start_server()

        overall_status = "success" if start_result["status"] == "success" else "failed"
        return {
            "stop_attempt": stop_result,
            "start_attempt": start_result,
            "overall_status": overall_status,
        }
