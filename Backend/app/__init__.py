from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

from app.config import Config
from app.utils.db import init_db

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)
    init_db(app)

    # Blueprints
    from app.routes.creator_routes       import creator_bp
    from app.routes.collaboration_routes import collaboration_bp
    from app.routes.pricing_routes       import pricing_bp
    from app.routes.risk_routes          import risk_bp
    from app.routes.creator_score_routes import score_bp
    from app.routes.analytics_routes     import analytics_bp
    from app.routes.instagram_routes     import instagram_bp
    from app.routes.brand_routes         import brand_bp

    app.register_blueprint(creator_bp, url_prefix="/api/creator")
    app.register_blueprint(collaboration_bp, url_prefix="/api/collaboration")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
    app.register_blueprint(instagram_bp, url_prefix="/api/instagram")
    app.register_blueprint(brand_bp, url_prefix="/api/brand")

    app.register_blueprint(pricing_bp)
    app.register_blueprint(risk_bp)
    app.register_blueprint(score_bp)

    @app.route("/")
    def health():
        return {"status": "CollabMind backend running"}, 200

    return app