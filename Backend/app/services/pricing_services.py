"""
app/services/pricing_services.py
=================================
Fetches a creator profile, computes a live creator_score via ML,
then runs the price-prediction model.
"""

from app.ml.predict     import run_prediction        # existing price model
from app.ml.ml_service  import predict_creator_score  # new creator score model
from app.utils.db       import get_db


def _fetch_profile(username: str):
    """Return the MongoDB document for username, or None."""
    db  = get_db()
    doc = db["profiles"].find_one({"profile.username": username})
    if doc is None:
        doc = db["creator_features"].find_one({"username": username})
    return doc


def _extract_features(doc: dict, live_score: float) -> dict:
    """
    Build the feature dict expected by the price model.
    Uses live_score (from creator_score_model) instead of a stored value.
    """
    p = doc.get("profile", doc)   # handle both nested and flat documents

    return {
        "followers":         float(p.get("follower_count",           p.get("followers",          0))),
        "following":         float(p.get("following_count",          p.get("following",          0))),
        "posts":             float(p.get("post_count",               p.get("posts",              0))),
        "engagement_rate":   float(p.get("engagement_rate",          0)),
        "avg_likes":         float(p.get("like_count_avg",           p.get("avg_likes",          0))),
        "avg_comments":      float(p.get("comment_count_avg",        p.get("avg_comments",       0))),
        "avg_views":         float(p.get("view_count_avg",           p.get("avg_views",          0))),
        "video_ratio":       float(p.get("video_ratio",              0)),
        "image_ratio":       float(p.get("image_ratio",              0)),
        "posting_frequency": float(p.get("posting_frequency_weekly", p.get("posting_frequency",  0))),
        "creator_score":     live_score,
    }


def _price_band(price: float) -> str:
    band = price * 0.15
    return f"₹{int(max(0, price - band)):,} - ₹{int(price + band):,}"


def predict_price(username: str) -> dict:
    username = username.strip().lower()

    doc = _fetch_profile(username)
    if doc is None:
        raise ValueError(f"Username '{username}' not found in database")

    # 1. Compute a fresh creator score via the ML model
    live_score = predict_creator_score(doc)

    # 2. Build feature vector for the price model
    features = _extract_features(doc, live_score)

    # 3. Run price model
    predicted_price = run_prediction(features)

    return {
        "username":        username,
        "predicted_price": predicted_price,
        "price_band":      _price_band(predicted_price),
        "creator_score":   live_score,
        "features_used":   features,
    }
