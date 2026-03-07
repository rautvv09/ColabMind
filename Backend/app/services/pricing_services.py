"""
app/services/pricing_services.py
=================================
Price prediction with auto-scrape fallback.
"""

import os

from app.ml.prediction    import run_prediction
from app.ml.ml_service import predict_creator_score
from app.utils.db      import get_db


def _fetch_profile(username: str):
    db  = get_db()
    doc = db["profiles"].find_one({"profile.username": username})
    if doc is None:
        doc = db["creator_features"].find_one({"username": username})
    return doc


def _extract_features(doc: dict, live_score: float) -> dict:
    p = doc.get("profile", doc)
    return {
        "followers":         float(p.get("follower_count",           p.get("followers",         0))),
        "following":         float(p.get("following_count",          p.get("following",         0))),
        "posts":             float(p.get("post_count",               p.get("posts",             0))),
        "engagement_rate":   float(p.get("engagement_rate",          0)),
        "avg_likes":         float(p.get("like_count_avg",           p.get("avg_likes",         0))),
        "avg_comments":      float(p.get("comment_count_avg",        p.get("avg_comments",      0))),
        "avg_views":         float(p.get("view_count_avg",           p.get("avg_views",         0))),
        "video_ratio":       float(p.get("video_ratio",              0)),
        "image_ratio":       float(p.get("image_ratio",              0)),
        "posting_frequency": float(p.get("posting_frequency_weekly", p.get("posting_frequency", 0))),
        "creator_score":     live_score,
    }


def _price_band(price: float) -> str:
    band = price * 0.15
    return f"₹{int(max(0, price - band)):,} - ₹{int(price + band):,}"


def predict_price(username: str) -> dict:
    username      = username.strip().lower()
    scraped_fresh = False

    doc = _fetch_profile(username)
    print(f"[pricing] _fetch_profile({username}) → {'found' if doc else 'NOT FOUND'}")

    if doc is None:
        api_key = os.getenv("SEARCHAPI_KEY", "")
        if not api_key:
            raise ValueError(
                f"'{username}' not in database and SEARCHAPI_KEY not set."
            )

        print(f"[pricing] Auto-scraping @{username}…")
        from app.services.scraper_service import scrape_and_store
        result = scrape_and_store(username, api_key, get_db())
        print(f"[pricing] scrape result → {result}")

        if result["status"] == "not_found":
            raise ValueError(f"Instagram profile '@{username}' not found or is private.")
        if result["status"] == "error":
            raise ValueError(f"Scraping failed: {result.get('message', '')}")

        doc = _fetch_profile(username)
        if doc is None:
            raise ValueError(f"Scraped @{username} but could not retrieve from DB.")

        scraped_fresh = True

    live_score      = predict_creator_score(doc)
    features        = _extract_features(doc, live_score)
    predicted_price = run_prediction(features)

    return {
        "username":        username,
        "predicted_price": predicted_price,
        "price_band":      _price_band(predicted_price),
        "creator_score":   live_score,
        "features_used":   features,
        "scraped_fresh":   scraped_fresh,
    }