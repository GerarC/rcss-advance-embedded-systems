from flask import Flask, jsonify

def create_app():
    app = Flask(__name__)
    
    from src.controllers.server_controller import server_bp 
    from src.controllers.bridge_controller import bridge_bp, bridge_service
    
    app.register_blueprint(server_bp) 
    app.register_blueprint(bridge_bp)

    @app.route('/')
    def index():
        return jsonify({'message': 'Welcome to the Flask API'})

    return app

if __name__ == '__main__':
    app = create_app()
    
    # Auto-start the bridge service (TCP port 5000)
    print("Starting Bridge Service...")
    from src.controllers.bridge_controller import bridge_service
    bridge_service.start()
    
    app.run(host='0.0.0.0', port=5001)
