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

    # Import blueprints
    from app.routes.creator_routes       import creator_bp
    from app.routes.collaboration_routes import collaboration_bp
    from app.routes.pricing_routes       import pricing_bp
    from app.routes.analytics_routes     import analytics_bp
    from app.routes.instagram_routes     import instagram_bp
    from app.routes.brand_routes         import brand_bp   # ⭐ ADD THIS

    # Register blueprints
    app.register_blueprint(creator_bp,       url_prefix="/api/creator")
    app.register_blueprint(collaboration_bp, url_prefix="/api/collaboration")
    app.register_blueprint(pricing_bp,       url_prefix="/api/ai")
    app.register_blueprint(analytics_bp,     url_prefix="/api/analytics")
    app.register_blueprint(instagram_bp,     url_prefix="/api/instagram")
    app.register_blueprint(brand_bp,         url_prefix="/api/brand")   # ⭐ ADD THIS

    @app.route("/")
    def health():
        return {"status": "CollabMind backend running"}, 200

    return app