import os
import joblib
import pandas as pd
from pymongo import MongoClient
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from dotenv import load_dotenv


# Load environment variables from .env
load_dotenv()


# Mongo config
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "instagram_db")
COLLECTION = "profiles"


# Paths
BASE_DIR = os.path.dirname(__file__)
MODEL_DIR = os.path.join(BASE_DIR, "models")

MODEL_PATH = os.path.join(MODEL_DIR, "price_model.joblib")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.joblib")


# Features used by the ML model
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

    if not MONGO_URI:
        raise ValueError("MONGO_URI not found. Check your .env file")

    print("Connecting to MongoDB Atlas...")

    client = MongoClient(MONGO_URI)

    db = client[DB_NAME]

    docs = list(db[COLLECTION].find({}))

    print("Documents fetched:", len(docs))

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

    os.makedirs(MODEL_DIR, exist_ok=True)

    df = fetch_data()

    if df.empty:
        raise ValueError("No data found in MongoDB collection")

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

    print("Training model...")

    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    mae = mean_absolute_error(y_test, preds)

    print("Model MAE:", round(mae, 2))

    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    print("Model saved to:", MODEL_PATH)
    print("Scaler saved to:", SCALER_PATH)


if __name__ == "__main__":
    train()