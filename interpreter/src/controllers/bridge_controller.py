from flask import Blueprint, jsonify, request
from src.services.bridge_service import BridgeService

bridge_bp = Blueprint('bridge', __name__, url_prefix='/api/v1/bridge')

# Singleton instance of the service
bridge_service = BridgeService()

@bridge_bp.route('/start', methods=['POST'])
def start_bridge():
    """Starts the bridge service."""
    result = bridge_service.start()
    http_status = 200 if result['status'] == 'success' else 400
    return jsonify(result), http_status

@bridge_bp.route('/stop', methods=['POST'])
def stop_bridge():
    """Stops the bridge service."""
    result = bridge_service.stop()
    http_status = 200 if result['status'] == 'success' else 400
    return jsonify(result), http_status

@bridge_bp.route('/status', methods=['GET'])
def get_status():
    """Returns the current status of the bridge."""
    return jsonify(bridge_service.get_status())

@bridge_bp.route('/command', methods=['POST'])
def send_command():
    """Sends a manual command to the RoboCup server."""
    data = request.get_json()
    if not data or 'command' not in data:
        return jsonify({"status": "error", "message": "Missing 'command' in body"}), 400
        
    result = bridge_service.send_command(data['command'])
    http_status = 200 if result['status'] == 'success' else 400
    return jsonify(result), http_status
