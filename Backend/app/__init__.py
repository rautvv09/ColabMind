from flask import Flask
from flask_cors import CORS
from app.config import Config
from app.utils.db import init_db


def create_app():

    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable CORS
    CORS(app)

    init_db(app)

    # ── Blueprints ─────────────────────────────────────────

    from app.routes.creator_routes import creator_bp
    from app.routes.collaboration_routes import collaboration_bp
    from app.routes.pricing_routes import pricing_bp
    from app.routes.risk_routes import risk_bp
    from app.routes.creator_score_routes import score_bp
    from app.routes.analytics_routes import analytics_bp
    from app.routes.instagram_routes import instagram_bp
    from app.routes.brand_routes import brand_bp

    # ── Register Blueprints ───────────────────────────────

    app.register_blueprint(creator_bp, url_prefix="/api/creator")

    app.register_blueprint(collaboration_bp, url_prefix="/api/collaboration")

    app.register_blueprint(pricing_bp)     # /api/ai/price

    app.register_blueprint(risk_bp)        # /api/ai/risk

    app.register_blueprint(score_bp)       # /api/ai/score

    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")

    app.register_blueprint(instagram_bp, url_prefix="/api/instagram")

    app.register_blueprint(brand_bp, url_prefix="/api/brand")

    # Health check
    @app.route("/")
    def health():
        return {"status": "CollabMind backend running"}, 200

    return app