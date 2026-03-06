"""
app/routes/pricing_routes.py
=============================
POST /api/ai/price/predict   { "username": "<handle>" }

Response includes `scraped_fresh` so the frontend can show the right
loading message ("Scraping new profile…" vs "Predicting…").
"""

from flask import Blueprint, request, jsonify
from app.services.pricing_services import predict_price

pricing_bp = Blueprint("pricing", __name__, url_prefix="/api/ai/price")


# ─────────────────────────────────────────────
# GET /api/ai/price/health
# ─────────────────────────────────────────────
@pricing_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "pricing"}), 200


# ─────────────────────────────────────────────
# POST /api/ai/price/predict
# Body: { "username": "bhuvan.bam22" }
#
# Success 200:
# {
#   "success": true,
#   "scraped_fresh": false,        ← true if the profile was just scraped
#   "data": {
#       "username": "...",
#       "predicted_price": 12500,
#       "price_band": "₹10,625 - ₹14,375",
#       "creator_score": 72.4,
#       "scraped_fresh": false,
#       "features_used": { ... }
#   }
# }
# ─────────────────────────────────────────────
@pricing_bp.route("/predict", methods=["POST"])
def predict():

    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "Request body missing"}), 400

    username = data.get("username")

    if not username:
        return jsonify({"success": False, "message": "username is required"}), 400

    try:
        result = predict_price(username.strip().lower())

        return jsonify({
            "success":       True,
            "scraped_fresh": result.get("scraped_fresh", False),
            "data":          result,
        }), 200

    except ValueError as e:
        # Covers: not found, private profile, scraping failed, no API key
        return jsonify({"success": False, "message": str(e)}), 404

    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Prediction failed",
            "detail":  str(e),
        }), 500