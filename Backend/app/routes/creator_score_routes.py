"""
app/routes/creator_score_routes.py
===================================
Blueprint: /api/ai/score

Endpoints
---------
GET  /api/ai/score/health
POST /api/ai/score/predict          – predict by username (DB lookup), writes score back
POST /api/ai/score/predict/features – predict from raw feature values (no DB)
"""

from flask import Blueprint, request, jsonify
from app.utils.db import get_db
from app.ml.ml_service import predict_creator_score, predict_from_raw

score_bp = Blueprint("creator_score", __name__, url_prefix="/api/ai/score")


# ── DB helper ─────────────────────────────────────────────────────────────────

def _get_doc_and_collection(username: str):
    """
    Returns (doc, collection_name) or raises ValueError.
    """
    db = get_db()

    doc = db["profiles"].find_one({"profile.username": username})
    if doc:
        return doc, "profiles"

    doc = db["creator_features"].find_one({"username": username})
    if doc:
        return doc, "creator_features"

    raise ValueError(f"Username '{username}' not found in database")


def _write_back(collection: str, doc_id, score: float):
    """Persist the computed creator_score back to MongoDB."""
    get_db()[collection].update_one(
        {"_id": doc_id},
        {"$set": {
            "creator_score":          score,
            "ml_output.creator_score": score,
        }}
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@score_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "creator_score"}), 200


@score_bp.route("/predict", methods=["POST"])
def predict():
    """
    Run the creator_score_model for a creator stored in MongoDB.
    Also writes the fresh score back to the document.

    Request body:  { "username": "instagramhandle" }

    Response:
    {
      "success": true,
      "data": {
        "username":      "instagramhandle",
        "creator_score": 7.42
      }
    }
    """
    body     = request.get_json(force=True, silent=True) or {}
    username = (body.get("username") or "").strip().lower()

    if not username:
        return jsonify({"success": False, "message": "username is required"}), 400

    try:
        doc, col = _get_doc_and_collection(username)
        score    = predict_creator_score(doc)
        _write_back(col, doc["_id"], score)

        return jsonify({
            "success": True,
            "data": {"username": username, "creator_score": score}
        }), 200

    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 404

    except Exception as exc:
        return jsonify({
            "success": False,
            "message": "Creator score prediction failed",
            "detail":  str(exc),
        }), 500


@score_bp.route("/predict/features", methods=["POST"])
def predict_features():
    """
    Run creator_score_model + risk model from raw input values (no DB).

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
        return jsonify({"success": True, "data": result}), 200

    except Exception as exc:
        return jsonify({
            "success": False,
            "message": "Prediction failed",
            "detail":  str(exc),
        }), 500