from flask import Blueprint, request, jsonify
from app.utils.db import get_db

risk_bp = Blueprint("risk", __name__, url_prefix="/api/ai/risk")


# Category → numeric score mapping (0‑1 probability-style)
_RISK_SCORE_MAP = {
    "LOW":     0.15,
    "MEDIUM":  0.55,
    "HIGH":    0.90,
    "UNKNOWN": 0.50,
}


def _fetch_risk(username: str):
    """
    Fetch pre-computed brand risk from the profiles collection.
    Returns (risk_label, risk_score) tuple.
    """
    db = get_db()
    doc = db["profiles"].find_one({"profile.username": username.lower()})

    if doc is None:
        raise ValueError(f"Username '{username}' not found in database")

    ml = doc.get("ml_output", {})

    # Try the nested brand_risk sub-document first
    brand_risk = ml.get("brand_risk", {})
    category   = brand_risk.get("brand_risk_category") or ml.get("brand_risk_category", "UNKNOWN")
    category   = (category or "UNKNOWN").upper()

    # Prefer stored composite risk score; fall back to the category map
    composite  = brand_risk.get("composite_risk_score")
    if composite is not None:
        risk_score = round(float(composite), 4)
    else:
        risk_score = _RISK_SCORE_MAP.get(category, 0.50)

    # Normalise label to title‑case for the UI
    label_map  = {"LOW": "Low", "MEDIUM": "Medium", "HIGH": "High", "UNKNOWN": "Unknown"}
    risk_label = label_map.get(category, "Unknown")

    return risk_label, risk_score


@risk_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "risk"}), 200


@risk_bp.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(force=True, silent=True)

    if not data:
        return jsonify({"success": False, "message": "Request body missing"}), 400

    username = data.get("username")

    if not username:
        return jsonify({"success": False, "message": "username is required"}), 400

    try:
        risk_label, risk_score = _fetch_risk(username.strip().lower())

        return jsonify({
            "success": True,
            "data": {
                "username":   username.strip().lower(),
                "risk_label": risk_label,
                "risk_score": risk_score,
            }
        }), 200

    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 404

    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Risk prediction failed",
            "detail":  str(e)
        }), 500