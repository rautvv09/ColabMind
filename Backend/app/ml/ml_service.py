"""
app/ml/ml_service.py
====================
Central ML service for CollabMind.

Loads two models once at startup (no per-request disk I/O):
  • creator_score_model.joblib  – RandomForestRegressor  – 9 features
  • Risk_Prediction_model.joblib – RandomForestClassifier – 6 features

Public API
----------
predict_creator_score(doc)   → float (0-10)
predict_risk(doc)             → dict  (risk_label, risk_score, probabilities …)
predict_from_raw(feat_dict)   → dict  (both models, no DB needed)
"""

import os
import logging
import warnings
import joblib
import numpy as np

logger = logging.getLogger(__name__)

# ── Model paths ────────────────────────────────────────────────────────────────
_BASE = os.path.dirname(os.path.abspath(__file__))

_SCORE_PATH = os.path.join(_BASE, "models", "creator_score_model.joblib")
_RISK_PATH  = os.path.join(_BASE, "models", "Risk_Prediction_model.joblib")

# ── Exact feature order as trained ────────────────────────────────────────────
#
# creator_score_model:  9 features
SCORE_FEATURES = [
    "followers",
    "following",
    "posts",
    "engagement",          # = profile["engagement_%"]
    "likes",               # = profile["like_count_avg"]
    "comments",            # = profile["comment_count_avg"]
    "posting_frequency",   # = profile["posting_frequency_weekly"]
    "video_ratio",
    "image_ratio",
]

# Risk_Prediction_model:  6 features
RISK_FEATURES = [
    "followers",
    "following",
    "posts",
    "engagement_percent",  # = profile["engagement_%"]
    "avg_likes",           # = profile["like_count_avg"]
    "avg_comments",        # = profile["comment_count_avg"]
]

# ── Risk label helpers ─────────────────────────────────────────────────────────
#   classifier classes: ['High Risk', 'Low Risk', 'Medium Risk']
_DISPLAY = {
    "High Risk":   "High",
    "Low Risk":    "Low",
    "Medium Risk": "Medium",
}
_COMPOSITE = {
    "High Risk":   0.90,
    "Low Risk":    0.15,
    "Medium Risk": 0.55,
}


# ── Load models at import time ─────────────────────────────────────────────────
def _load(path: str, name: str):
    if not os.path.exists(path):
        raise RuntimeError(
            f"[ml_service] {name} not found at:\n  {path}\n"
            "Copy the .joblib file to app/ml/models/"
        )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = joblib.load(path)
    logger.info("[ml_service] Loaded %s", name)
    return m


_score_model = _load(_SCORE_PATH, "creator_score_model")
_risk_model  = _load(_RISK_PATH,  "Risk_Prediction_model")


# ── Internal helper: flatten a MongoDB profile document ───────────────────────
def _flatten(doc: dict) -> dict:
    """
    Returns a flat feature dict from a MongoDB document.
    Handles both shapes:
      • { profile: { follower_count: … } }   (scraped profiles collection)
      • { follower_count: …, engagement_rate: … }  (creator_features collection)
    """
    p = doc.get("profile", doc)  # use nested profile if present, else root

    followers  = float(p.get("follower_count",          p.get("followers",         0)))
    following  = float(p.get("following_count",          p.get("following",         0)))
    posts      = float(p.get("post_count",               p.get("posts",             0)))
    eng_pct    = float(p.get("engagement_%",             0))   # stored as % (e.g. 3.5)
    likes      = float(p.get("like_count_avg",           p.get("avg_likes",         0)))
    comments   = float(p.get("comment_count_avg",        p.get("avg_comments",      0)))
    freq       = float(p.get("posting_frequency_weekly", p.get("posting_frequency", 0)))
    vid_ratio  = float(p.get("video_ratio",  0))
    img_ratio  = float(p.get("image_ratio",  0))

    return {
        # score model keys
        "followers":         followers,
        "following":         following,
        "posts":             posts,
        "engagement":        eng_pct,
        "likes":             likes,
        "comments":          comments,
        "posting_frequency": freq,
        "video_ratio":       vid_ratio,
        "image_ratio":       img_ratio,
        # risk model keys (overlap)
        "engagement_percent": eng_pct,
        "avg_likes":          likes,
        "avg_comments":       comments,
    }


# ── Public functions ───────────────────────────────────────────────────────────

def predict_creator_score(doc: dict) -> float:
    """
    Predict creator score (0–10) from a MongoDB profile document.

    Parameters
    ----------
    doc : dict  – document from the 'profiles' or 'creator_features' collection

    Returns
    -------
    float – score clamped to [0, 10], rounded to 4 d.p.
    """
    feat   = _flatten(doc)
    vector = np.array([[feat[k] for k in SCORE_FEATURES]])
    score  = float(_score_model.predict(vector)[0])
    return round(max(0.0, min(10.0, score)), 4)


def predict_risk(doc: dict) -> dict:
    """
    Predict brand collaboration risk from a MongoDB profile document.

    Returns
    -------
    dict with:
        risk_category  – "Low Risk" | "Medium Risk" | "High Risk"
        risk_label     – "Low" | "Medium" | "High"
        risk_score     – float 0-1 (probability of High Risk)
        probabilities  – { "High Risk": 0.12, "Low Risk": 0.76, "Medium Risk": 0.12 }
    """
    feat   = _flatten(doc)
    vector = np.array([[feat[k] for k in RISK_FEATURES]])

    raw_label = _risk_model.predict(vector)[0]          # e.g. "Low Risk"

    # Per-class probability distribution
    proba = {}
    if hasattr(_risk_model, "predict_proba"):
        probs = _risk_model.predict_proba(vector)[0]
        proba = {cls: round(float(p), 4)
                 for cls, p in zip(_risk_model.classes_, probs)}

    # Use P(High Risk) as the composite risk score; fall back to bucket default
    composite = proba.get("High Risk", _COMPOSITE.get(raw_label, 0.50))

    return {
        "risk_category": raw_label,
        "risk_label":    _DISPLAY.get(raw_label, raw_label),
        "risk_score":    round(float(composite), 4),
        "probabilities": proba,
    }


def predict_from_raw(feature_dict: dict) -> dict:
    """
    Run both models from a plain feature dictionary (no DB document needed).

    Accepted keys (all optional, default 0):
        followers, following, posts, engagement_percent,
        avg_likes, avg_comments, posting_frequency,
        video_ratio, image_ratio

    Returns
    -------
    dict with creator_score + all risk fields
    """
    pseudo_profile = {
        "follower_count":           float(feature_dict.get("followers",           0)),
        "following_count":          float(feature_dict.get("following",           0)),
        "post_count":               float(feature_dict.get("posts",               0)),
        "engagement_%":             float(feature_dict.get("engagement_percent",  0)),
        "like_count_avg":           float(feature_dict.get("avg_likes",           0)),
        "comment_count_avg":        float(feature_dict.get("avg_comments",        0)),
        "posting_frequency_weekly": float(feature_dict.get("posting_frequency",   0)),
        "video_ratio":              float(feature_dict.get("video_ratio",         0)),
        "image_ratio":              float(feature_dict.get("image_ratio",         0)),
    }
    doc = {"profile": pseudo_profile}

    score  = predict_creator_score(doc)
    risk   = predict_risk(doc)

    return {"creator_score": score, **risk}
