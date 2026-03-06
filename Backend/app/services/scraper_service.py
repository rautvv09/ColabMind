"""
app/services/scraper_service.py
================================
Bridge between the Flask backend and the SearchAPI scraper pipeline.

Exposes one public function:
    scrape_and_store(username, api_key, db) -> dict
        { "status": "success"|"not_found"|"error", "action": str, "message": str }

Internally calls:
    app/scraper/profile.py  →  process_profile()
    app/scraper/brand.py    →  process_brand_collabs()

These are the same modules used by the Streamlit app (app.py), so the
MongoDB document schema stays identical and pricing_services.py can read
scraped documents without any changes to its field lookups.
"""

import sys
import os

# ── Make sure app/scraper/ is importable ─────────────────────
_scraper_dir = os.path.join(os.path.dirname(__file__), "..", "scraper")
if _scraper_dir not in sys.path:
    sys.path.insert(0, os.path.abspath(_scraper_dir))

from profile import process_profile          # app/scraper/profile.py
from brand   import process_brand_collabs    # app/scraper/brand.py


def scrape_and_store(username: str, api_key: str, db) -> dict:
    """
    Scrape an Instagram profile via SearchAPI and store the results in
    the same MongoDB collections used by the Streamlit scraper:
        instagram_db.profiles        (profile + posts)
        instagram_db.brand_collabs   (collab & brand data)

    Parameters
    ----------
    username : str
        Instagram username (no @).
    api_key  : str
        SearchAPI key from config / env.
    db       : pymongo.database.Database
        Live database handle — typically get_db() from app.utils.db.

    Returns
    -------
    dict with keys:
        status  – "success" | "not_found" | "error"
        action  – "inserted" | "updated" | "no_change" | None
        message – human-readable detail (populated on error/not_found)
    """
    username = username.strip().lower()

    profiles_col   = db["profiles"]
    brand_col      = db["brand_collabs"]

    # ── Step 1: Fetch, parse, and save the profile ────────────
    p_result = process_profile(
        username            = username,
        api_key             = api_key,
        profiles_collection = profiles_col,
        max_posts           = 30,
        with_collab         = True,
    )

    if p_result["status"] == "not_found":
        return {
            "status":  "not_found",
            "action":  None,
            "message": f"Instagram profile '@{username}' not found.",
        }

    if p_result["status"] == "error":
        return {
            "status":  "error",
            "action":  None,
            "message": p_result.get("message", "Scraping failed."),
        }

    profile_record = p_result["profile_record"]
    post_rows      = p_result["post_rows"]
    p_action       = p_result["action"]           # "inserted" | "updated" | "no_change"

    # ── Step 2: Detect brand collaborations ──────────────────
    try:
        b_result = process_brand_collabs(
            profile_record   = profile_record,
            post_rows        = post_rows,
            brand_collection = brand_col,
        )
        b_action = b_result.get("action", "ok")
    except Exception as e:
        # Brand collabs are non-critical — log but don't fail
        b_action = f"brand_error: {e}"

    return {
        "status":  "success",
        "action":  p_action,          # what happened to the profiles collection
        "b_action": b_action,         # what happened to brand_collabs
        "message": f"Scraped and stored '@{username}' (profiles: {p_action}, brand_collabs: {b_action})",
    }