from flask import Flask, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os, time

load_dotenv()

def create_app():
    app = Flask(__name__)
    CORS(app)

    from app.crisisfeed_config import get_config
    app.config.from_object(get_config())

    from app.crisisfeed_errors import register_error_handlers
    register_error_handlers(app)

    from app.routes.crisisfeed_points   import points_bp
    from app.routes.crisisfeed_crisis   import crisis_bp
    from app.routes.crisisfeed_forecast import forecast_bp
    from app.routes.crisisfeed_gemini   import gemini_bp
    from app.routes.crisisfeed_global   import global_bp
    from app.routes.crisisfeed_health   import health_bp
    from app.routes.crisisfeed_model   import model_bp

    app.register_blueprint(points_bp,   url_prefix='/api')
    app.register_blueprint(crisis_bp,   url_prefix='/api')
    app.register_blueprint(forecast_bp, url_prefix='/api')
    app.register_blueprint(gemini_bp,   url_prefix='/api')
    app.register_blueprint(global_bp,   url_prefix='/api')
    app.register_blueprint(health_bp,   url_prefix='/api')
    app.register_blueprint(model_bp,    url_prefix='/api')

    @app.route('/')
    def index():
        static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../static'))
        return send_from_directory(static_dir, 'crisisfeed_dashboard.html')

    return app
