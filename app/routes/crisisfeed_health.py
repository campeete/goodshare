import os
from flask import Blueprint, current_app
from app.crisisfeed_errors import success_response
from app.crisisfeed_logger import get_logger

logger = get_logger(__name__)
health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    data_dir = os.path.join(os.path.dirname(__file__), '../../data/seed')
    gemini_ok = bool(os.environ.get('GEMINI_API_KEY'))
    return success_response({
        'status': 'ok',
        'version': current_app.config.get('API_VERSION', '1.0.0'),
        'app': current_app.config.get('APP_NAME', 'CrisisFeed'),
        'environment': os.environ.get('FLASK_ENV', 'development'),
        'gemini_configured': gemini_ok,
        'data_sources': {
            'who_global':    'loaded' if os.path.exists(os.path.join(data_dir, 'crisisfeed_global_data.json')) else 'missing',
            'dc_food_points': 'loaded' if os.path.exists(os.path.join(data_dir, 'food_points.json')) else 'missing',
        }
    })
