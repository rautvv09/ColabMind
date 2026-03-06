"""
app/routes/risk_routes.py
=========================
Blueprint: /api/ai/risk

Endpoints
---------
GET  /api/ai/risk/health
POST /api/ai/risk/predict          – predict by Instagram username (DB lookup)
POST /api/ai/risk/predict/features – predict from raw feature values (no DB)
"""

from flask import Blueprint, request, jsonify
from app.utils.db import get_db
from app.ml.ml_service import predict_risk, predict_from_raw

risk_bp = Blueprint("risk", __name__, url_prefix="/api/ai/risk")


# ── DB helper ─────────────────────────────────────────────────────────────────

def _get_doc(username: str) -> dict:
    """
    Fetch a profile document by username.
    Tries the 'profiles' collection first (scraped docs),
    then 'creator_features' (registered creators).
    Raises ValueError if not found.
    """
    db  = get_db()
    doc = db["profiles"].find_one({"profile.username": username})
    if doc is None:
        doc = db["creator_features"].find_one({"username": username})
    if doc is None:
        raise ValueError(f"Username '{username}' not found in database")
    return doc


# ── Routes ────────────────────────────────────────────────────────────────────

@risk_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "risk"}), 200


@risk_bp.route("/predict", methods=["POST"])
def predict():
    """
    Run the Risk_Prediction_model for a creator stored in MongoDB.

    Request body:  { "username": "instagramhandle" }

    Response:
    {
      "success": true,
      "data": {
        "username":      "instagramhandle",
        "risk_category": "Low Risk",
        "risk_label":    "Low",
        "risk_score":    0.12,
        "probabilities": { "High Risk": 0.12, "Low Risk": 0.76, "Medium Risk": 0.12 }
      }
    }
    """
    body = request.get_json(force=True, silent=True) or {}

    username = (body.get("username") or "").strip().lower()
    if not username:
        return jsonify({"success": False, "message": "username is required"}), 400

    try:
        doc    = _get_doc(username)
        result = predict_risk(doc)

        return jsonify({
            "success": True,
            "data": {"username": username, **result}
        }), 200

    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 404

    except Exception as exc:
        return jsonify({
            "success": False,
            "message": "Risk prediction failed",
            "detail":  str(exc),
        }), 500


@risk_bp.route("/predict/features", methods=["POST"])
def predict_features():
    """
    Run the Risk_Prediction_model from raw input values (no DB lookup).

    Request body:
    {
      "followers": 50000, "following": 300, "posts": 120,
      "engagement_percent": 3.5, "avg_likes": 1800, "avg_comments": 90,
      "posting_frequency": 4, "video_ratio": 0.4, "image_ratio": 0.6
    }
    """
    body = request.get_json(force=True, silent=True) or {}
    if not body:
        return jsonify({"success": False, "message": "Request body missing"}), 400

    try:
        result = predict_from_raw(body)
        return jsonify({
            "success": True,
            "data": {
                "risk_category": result["risk_category"],
                "risk_label":    result["risk_label"],
                "risk_score":    result["risk_score"],
                "probabilities": result["probabilities"],
                "creator_score": result["creator_score"],
            }
        }), 200

    except Exception as exc:
        return jsonify({
            "success": False,
            "message": "Risk prediction failed",
            "detail":  str(exc),
        }), 500
