"""
app/ml/predict.py
==================
Thin wrapper that exposes run_prediction(feature_dict) -> float
for use by pricing_services.py.

Uses price_model.joblib + price_scaler.joblib (the files present after merge).
The old scaler.joblib was removed in the merge; price_scaler.joblib is its
replacement with the same purpose.
"""

import os
import joblib
import numpy as np

_BASE   = os.path.dirname(os.path.abspath(__file__))
_MODELS = os.path.join(_BASE, "models")

_MODEL_PATH  = os.path.join(_MODELS, "price_model.joblib")
_SCALER_PATH = os.path.join(_MODELS, "scaler.joblib")   # price_scaler.joblib has 28 features; scaler.joblib matches the 11-feature price_model

FEATURES = [
    "followers",
    "following",
    "posts",
    "engagement_rate",
    "avg_likes",
    "avg_comments",
    "avg_views",
    "video_ratio",
    "image_ratio",
    "posting_frequency",
    "creator_score",
]

# Load once at import time
if not os.path.exists(_MODEL_PATH):
    raise RuntimeError(f"price_model.joblib not found at {_MODEL_PATH}")
if not os.path.exists(_SCALER_PATH):
    raise RuntimeError(f"scaler.joblib not found at {_SCALER_PATH}")

_model  = joblib.load(_MODEL_PATH)
_scaler = joblib.load(_SCALER_PATH)


def run_prediction(feature_dict: dict) -> float:
    """
    Predict collaboration price from a feature dictionary.

    Parameters
    ----------
    feature_dict : dict  — keys match FEATURES list above (missing → 0)

    Returns
    -------
    float  — predicted price in INR, rounded to 2 d.p.
    """
    vector = np.array([
        [float(feature_dict.get(f, 0)) for f in FEATURES]
    ])
    scaled     = _scaler.transform(vector)
    prediction = _model.predict(scaled)[0]
    return round(float(prediction), 2)