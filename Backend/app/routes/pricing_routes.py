from flask import Blueprint, request
from bson import ObjectId

from app.config import Config
from app.utils.db import get_collection
from app.utils.helpers import success_response, error_response
from app.utils.validators import is_valid_object_id, validate_required_fields

pricing_bp = Blueprint("pricing", __name__)


# ─── POST /api/ai/price/predict ──────────────────────────────────────────────
@pricing_bp.route("/price/predict", methods=["POST"])
def predict_price():
    """
    Accepts creator metrics directly or a creator_id to look up from DB.
    Returns recommended price and confidence score.
    """
    data = request.get_json() or {}

    # If creator_id supplied, fetch metrics from DB
    if "creator_id" in data:
        if not is_valid_object_id(data["creator_id"]):
            return error_response("Invalid creator_id.")
        doc = get_collection(Config.COLLECTION_CREATORS).find_one(
            {"_id": ObjectId(data["creator_id"])}
        )
        if not doc:
            return error_response("Creator not found.", 404)
        features = _extract_price_features(doc)
    else:
        # Manual feature input
        missing = validate_required_fields(data, [
            "followers", "avg_likes", "avg_comments",
            "avg_reel_views", "niche", "avg_deal_value"
        ])
        if missing:
            return error_response(f"Missing fields: {', '.join(missing)}")
        features = _extract_price_features(data)

    try:
        from app.ml.predict import predict_price as ml_predict
        result = ml_predict(features)
    except Exception as e:
        # Fallback: rule-based estimate if model not yet trained
        result = _rule_based_price(features)
        result["note"] = "ML model not loaded; rule-based estimate used."

    return success_response(result)


# ─── POST /api/ai/risk/predict ───────────────────────────────────────────────
@pricing_bp.route("/risk/predict", methods=["POST"])
def predict_risk():
    """
    Accepts brand metrics or a brand_id.
    Returns risk_label (Low/Medium/High) and risk_score.
    Persists result back to brand document.
    """
    data = request.get_json() or {}

    if "brand_id" in data:
        if not is_valid_object_id(data["brand_id"]):
            return error_response("Invalid brand_id.")
        doc = get_collection(Config.COLLECTION_BRANDS).find_one(
            {"_id": ObjectId(data["brand_id"])}
        )
        if not doc:
            return error_response("Brand not found.", 404)
        features = _extract_risk_features(doc)
        brand_id = data["brand_id"]
    else:
        missing = validate_required_fields(data, [
            "avg_payment_delay_days", "late_payment_count",
            "total_deals", "deal_completion_rate"
        ])
        if missing:
            return error_response(f"Missing fields: {', '.join(missing)}")
        features = _extract_risk_features(data)
        brand_id = None

    try:
        from app.ml.predict import predict_risk as ml_predict_risk
        result = ml_predict_risk(features)
    except Exception:
        result = _rule_based_risk(features)
        result["note"] = "ML model not loaded; rule-based estimate used."

    # Persist risk back to brand document
    if brand_id:
        from app.models.brand import BrandModel
        get_collection(Config.COLLECTION_BRANDS).update_one(
            {"_id": ObjectId(brand_id)},
            BrandModel.update_risk(result["risk_label"], result["risk_score"])
        )

    return success_response(result)


# ─── GET /api/ai/features/<creator_id> ───────────────────────────────────────
@pricing_bp.route("/features/<creator_id>", methods=["GET"])
def get_feature_vector(creator_id):
    """Return the computed feature vector used as ML model input."""
    if not is_valid_object_id(creator_id):
        return error_response("Invalid creator ID.")

    doc = get_collection(Config.COLLECTION_CREATORS).find_one(
        {"_id": ObjectId(creator_id)}
    )
    if not doc:
        return error_response("Creator not found.", 404)

    return success_response(_extract_price_features(doc))


# ─── Private helpers ─────────────────────────────────────────────────────────

def _extract_price_features(doc: dict) -> dict:
    followers    = float(doc.get("followers", 0))
    avg_likes    = float(doc.get("avg_likes", 0))
    avg_comments = float(doc.get("avg_comments", 0))
    avg_views    = float(doc.get("avg_reel_views", 0))
    er = ((avg_likes + avg_comments) / followers * 100) if followers else 0.0
    return {
        "followers":            followers,
        "avg_likes":            avg_likes,
        "avg_comments":         avg_comments,
        "avg_reel_views":       avg_views,
        "engagement_rate":      round(er, 4),
        "niche":                doc.get("niche", "other"),
        "avg_deal_value":       float(doc.get("avg_deal_value", 0)),
        "posting_consistency":  float(doc.get("posting_consistency_score", 0.5)),
        "creator_score":        float(doc.get("creator_score", 5.0)),
    }


def _extract_risk_features(doc: dict) -> dict:
    return {
        "avg_payment_delay_days": float(doc.get("avg_payment_delay_days", 0)),
        "late_payment_count":     float(doc.get("late_payment_count", 0)),
        "total_deals":            float(doc.get("total_deals", 0)),
        "deal_completion_rate":   float(doc.get("deal_completion_rate", 1.0)),
    }


def _rule_based_price(f: dict) -> dict:
    """Simple fallback pricing formula."""
    base  = f["followers"] * 0.01
    er_b  = f["engagement_rate"] * 500
    niche_mult = {"tech": 1.4, "finance": 1.4, "fashion": 1.2,
                  "beauty": 1.2, "fitness": 1.1}.get(f["niche"], 1.0)
    price = (base + er_b) * niche_mult
    return {"recommended_price": round(price, 2), "confidence_score": 0.6}


def _rule_based_risk(f: dict) -> dict:
    delay = f["avg_payment_delay_days"]
    rate  = f["deal_completion_rate"]
    if delay > 30 or rate < 0.6:
        label, score = "High",   0.8
    elif delay > 10 or rate < 0.85:
        label, score = "Medium", 0.5
    else:
        label, score = "Low",    0.2
    return {"risk_label": label, "risk_score": score}
