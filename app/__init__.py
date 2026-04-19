from flask import Flask, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    CORS(app)

    from app.routes.goodshare_points import points_bp
    from app.routes.goodshare_crisis import crisis_bp
    from app.routes.goodshare_forecast import forecast_bp
    from app.routes.goodshare_gemini import gemini_bp
    from app.routes.goodshare_global import global_bp

    app.register_blueprint(points_bp, url_prefix='/api')
    app.register_blueprint(crisis_bp, url_prefix='/api')
    app.register_blueprint(forecast_bp, url_prefix='/api')
    app.register_blueprint(gemini_bp, url_prefix='/api')
    app.register_blueprint(global_bp, url_prefix='/api')

    @app.route('/')
    def index():
        static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../static'))
        return send_from_directory(static_dir, 'crisisfeed_dashboard.html')

    return app
