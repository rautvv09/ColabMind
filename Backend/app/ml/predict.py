import os
import joblib
import numpy as np


BASE_DIR = os.path.dirname(__file__)

MODEL_PATH = os.path.join(BASE_DIR, "models", "price_model.joblib")
SCALER_PATH = os.path.join(BASE_DIR, "models", "scaler.joblib")


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
    "creator_score"
]


model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)


def run_prediction(feature_dict):

    vector = np.array([[feature_dict[f] for f in FEATURES]])

    scaled = scaler.transform(vector)

    prediction = model.predict(scaled)[0]

    return round(float(prediction), 2)