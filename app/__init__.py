from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config['GEMINI_KEY'] = os.getenv('GEMINI_API_KEY')
    app.db = None
    from app.routes.points import points_bp
    from app.routes.forecast import forecast_bp
    from app.routes.crisis import crisis_bp
    app.register_blueprint(points_bp, url_prefix='/api')
    app.register_blueprint(forecast_bp, url_prefix='/api')
    app.register_blueprint(crisis_bp, url_prefix='/api')
    return app
