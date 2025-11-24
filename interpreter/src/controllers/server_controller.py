from flask import Blueprint, jsonify
from src.services.server_service import ServerManager

server_bp = Blueprint('server', __name__, url_prefix='/api/v1/server')

manager = ServerManager()

@server_bp.route('/status', methods=['GET'])
def server_status():
    """Returns the current status of the server."""
    return jsonify(manager.get_status())

@server_bp.route('/start', methods=['POST'])
def start_server():
    """Starts the rcssserver."""
    result = manager.start_server()
    http_status = 200 if result['status'] == 'success' else 400
    return jsonify(result), http_status

@server_bp.route('/stop', methods=['POST'])
def stop_server():
    """Stops the rcssserver."""
    result = manager.stop_server()
    http_status = 200 if result['status'] == 'success' else 400
    return jsonify(result), http_status

@server_bp.route('/restart', methods=['POST'])
def restart_server():
    """Restarts the rcssserver."""
    result = manager.restart_server()
    http_status = 200 if result['overall_status'] == 'success' else 400
    return jsonify(result), http_status
