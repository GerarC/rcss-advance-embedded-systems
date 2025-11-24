from flask import Flask, jsonify

def create_app():
    app = Flask(__name__)
    
    from src.controllers.server_controller import server_bp 
    
    app.register_blueprint(server_bp) 

    @app.route('/')
    def index():
        return jsonify({'message': 'Welcome to the Flask API'})

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
