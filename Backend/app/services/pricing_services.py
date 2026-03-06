"""
app/services/pricing_services.py
=================================
Fetches a creator profile, computes a live creator_score via ML,
then runs the price-prediction model.

NEW behaviour
-------------
If the username is NOT already in MongoDB, the service automatically:
  1. Calls scraper_service.scrape_and_store() to fetch from SearchAPI
     and write to the `profiles` + `brand_collabs` collections.
  2. Re-queries the profile.
  3. Proceeds with prediction as normal.

This means the frontend only needs to call /api/ai/price/predict once —
the backend handles the "new user" case transparently.
"""

import os
from flask import current_app

from app.ml.predict     import run_prediction          # price model
from app.ml.ml_service  import predict_creator_score   # creator score model
from app.utils.db       import get_db


# ─────────────────────────────────────────────────────────────
#  Internal helpers
# ─────────────────────────────────────────────────────────────

def _fetch_profile(username: str):
    """Return the MongoDB document for username, or None."""
    db  = get_db()
    doc = db["profiles"].find_one({"profile.username": username})
    if doc is None:
        # fallback: flat-schema documents (creator_features collection)
        doc = db["creator_features"].find_one({"username": username})
    return doc


def _extract_features(doc: dict, live_score: float) -> dict:
    """
    Build the feature dict expected by the price model.
    Handles both nested {profile: {...}} and flat document shapes.
    """
    p = doc.get("profile", doc)

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


# ─────────────────────────────────────────────────────────────
#  Public entry point
# ─────────────────────────────────────────────────────────────

def predict_price(username: str) -> dict:
    """
    Predict collaboration price for an Instagram username.

    Flow:
        1. Look up username in MongoDB.
        2. If NOT found  → scrape via SearchAPI, store, then re-fetch.
        3. Compute live creator_score via ML model.
        4. Run price model.
        5. Return result dict (includes `scraped_fresh` flag).

    Raises:
        ValueError  – if username not found on Instagram OR scraping fails.
        Exception   – on unexpected ML / DB errors.
    """
    username = username.strip().lower()

    # ── 1. Check DB ───────────────────────────────────────────
    doc = _fetch_profile(username)
    scraped_fresh = False

    # ── 2. Auto-scrape if missing ─────────────────────────────
    if doc is None:
        api_key = os.getenv("SEARCHAPI_KEY", "")

        if not api_key:
            raise ValueError(
                f"Username '{username}' is not in the database and "
                "SEARCHAPI_KEY is not set — cannot auto-scrape."
            )

        # Import here to avoid circular dependency at module load time
        from app.services.scraper_service import scrape_and_store

        db     = get_db()
        result = scrape_and_store(username, api_key, db)

        if result["status"] == "not_found":
            raise ValueError(
                f"Instagram profile '@{username}' does not exist or is private."
            )
        if result["status"] == "error":
            raise ValueError(
                f"Scraping failed for '@{username}': {result.get('message', '')}"
            )

        # Re-fetch the freshly stored document
        doc = _fetch_profile(username)
        if doc is None:
            raise ValueError(
                f"Profile '@{username}' was scraped but could not be retrieved. "
                "Check MongoDB write permissions."
            )

        scraped_fresh = True

    # ── 3. Live creator score ─────────────────────────────────
    live_score = predict_creator_score(doc)

    # ── 4. Price prediction ───────────────────────────────────
    features        = _extract_features(doc, live_score)
    predicted_price = run_prediction(features)

    return {
        "username":        username,
        "predicted_price": predicted_price,
        "price_band":      _price_band(predicted_price),
        "creator_score":   live_score,
        "scraped_fresh":   scraped_fresh,   # True = was just scraped for the first time
        "features_used":   features,
    }