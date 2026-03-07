import os
from dotenv import load_dotenv

load_dotenv()   # <-- THIS LINE IS REQUIRED

class Config:

    MONGO_URI = os.getenv("MONGO_URI")
    DB_NAME = os.getenv("DB_NAME", "instagram_db")

    FLASK_DEBUG = os.getenv("FLASK_DEBUG", True)
    PORT = int(os.getenv("PORT", 5000))

    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")

    # Mongo collections
    COLLECTION_CREATORS = "profiles"
    COLLECTION_COLLABORATIONS = "collaborations"
    COLLECTION_BRANDS = "brands"