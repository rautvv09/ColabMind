import os

class Config:
    MONGO_URI = os.getenv("MONGO_URI")
    DB_NAME = os.getenv("DB_NAME", "instagram_db")
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", False)
    PORT = int(os.getenv("PORT", 5000))