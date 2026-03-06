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


# Load model artifacts
if not os.path.exists(MODEL_PATH):
    raise RuntimeError("price_model.joblib not found. Train model first.")

if not os.path.exists(SCALER_PATH):
    raise RuntimeError("scaler.joblib not found. Train model first.")


model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)


def run_prediction(feature_dict):

    try:

        vector = np.array([
            [float(feature_dict.get(feature, 0)) for feature in FEATURES]
        ])

        scaled = scaler.transform(vector)

        prediction = model.predict(scaled)[0]

        return round(float(prediction), 2)

    except Exception as e:
        raise RuntimeError(f"ML prediction failed: {str(e)}")