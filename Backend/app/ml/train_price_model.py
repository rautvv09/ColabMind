import os
import joblib
import pandas as pd
from pymongo import MongoClient
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error


MONGO_URI = os.getenv("MONGO_URI")

DB_NAME = "instagram_db"
COLLECTION = "profiles"


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


def fetch_data():

    client = MongoClient(MONGO_URI)

    docs = list(client[DB_NAME][COLLECTION].find({}))

    rows = []

    for doc in docs:

        profile = doc.get("profile", {})
        ml = doc.get("ml_output", {})

        followers = profile.get("follower_count", 0)
        avg_likes = profile.get("like_count_avg", 0)
        engagement = profile.get("engagement_rate", 0)
        creator_score = ml.get("creator_score", 0)

        estimated_price = (
            followers * 0.01 +
            avg_likes * 0.15 +
            engagement * 800 +
            creator_score * 120
        )

        rows.append({

            "followers": followers,
            "following": profile.get("following_count", 0),
            "posts": profile.get("post_count", 0),

            "engagement_rate": engagement,

            "avg_likes": avg_likes,
            "avg_comments": profile.get("comment_count_avg", 0),
            "avg_views": profile.get("view_count_avg", 0),

            "video_ratio": profile.get("video_ratio", 0),
            "image_ratio": profile.get("image_ratio", 0),

            "posting_frequency": profile.get("posting_frequency_weekly", 0),

            "creator_score": creator_score,

            "estimated_price": estimated_price

        })

    return pd.DataFrame(rows)


def train():

    os.makedirs(os.path.join(BASE_DIR, "models"), exist_ok=True)

    df = fetch_data()

    X = df[FEATURES]
    y = df["estimated_price"]

    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled,
        y,
        test_size=0.2,
        random_state=42
    )

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=10,
        random_state=42
    )

    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    mae = mean_absolute_error(y_test, preds)

    print("MAE:", mae)

    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    print("Model saved")


if __name__ == "__main__":
    train()