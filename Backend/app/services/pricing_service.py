import numpy as np
from app.ml.predict import run_prediction
from app.utils.db import get_db


COLLECTION = "profiles"


def fetch_profile(username):

    db = get_db()

    doc = db[COLLECTION].find_one({
        "profile.username": username
    })

    return doc


def extract_features(doc):

    profile = doc.get("profile", {})
    ml = doc.get("ml_output", {})

    features = {

        "followers": float(profile.get("follower_count", 0)),
        "following": float(profile.get("following_count", 0)),
        "posts": float(profile.get("post_count", 0)),

        "engagement_rate": float(profile.get("engagement_rate", 0)),
        "avg_likes": float(profile.get("like_count_avg", 0)),
        "avg_comments": float(profile.get("comment_count_avg", 0)),
        "avg_views": float(profile.get("view_count_avg", 0)),

        "video_ratio": float(profile.get("video_ratio", 0)),
        "image_ratio": float(profile.get("image_ratio", 0)),

        "posting_frequency": float(profile.get("posting_frequency_weekly", 0)),

        "creator_score": float(ml.get("creator_score", 0))

    }

    return features


def build_price_band(price):

    band = price * 0.15

    low = max(0, price - band)
    high = price + band

    return f"₹{int(low):,} - ₹{int(high):,}"


def predict_price(username):

    doc = fetch_profile(username)

    if doc is None:
        raise ValueError("username not found")

    features = extract_features(doc)

    predicted_price = run_prediction(features)

    return {

        "username": username,

        "predicted_price": predicted_price,

        "price_band": build_price_band(predicted_price),

        "features_used": features
    }