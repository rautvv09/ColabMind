import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI      = os.getenv("MONGO_URI", "")
    DB_NAME        = os.getenv("DB_NAME", "collabmind")
    SECRET_KEY     = os.getenv("SECRET_KEY", "dev-secret-key")
    FLASK_DEBUG    = os.getenv("FLASK_DEBUG", "True") == "True"
    PORT           = int(os.getenv("PORT", 5000))
    INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")

    # MongoDB collection names
    COLLECTION_CREATORS       = "profiles"
    COLLECTION_COLLABORATIONS = "collaborations"
