from pymongo import MongoClient
from flask import current_app, g

_client: MongoClient = None

def init_db(app):
    """Initialize MongoDB client and attach to app context."""
    global _client
    _client = MongoClient(app.config["MONGO_URI"])
    app.extensions["mongo"] = _client
    app.teardown_appcontext(close_db)

def get_db():
    """Return the database instance. Works inside and outside request context."""
    if "db" not in g:
        g.db = _client[current_app.config["DB_NAME"]]
    return g.db

def close_db(error=None):
    g.pop("db", None)

def get_collection(name: str):
    """Shortcut to get a specific collection."""
    return get_db()[name]
