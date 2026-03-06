"""
================================================================================
  prediction.py  —  Influencer Collaboration Price Predictor
  Input  : Instagram username (CLI or function call)
  Output : Collaboration price in INR + brand risk + creator score
================================================================================

  USAGE:
    python prediction.py cristiano
    python prediction.py zakirkhan_208
    python prediction.py                    ← interactive prompt

  REQUIRES:
    1. atlas_pipeline_runner.py must have been run first
       (writes feature vectors to instagram_db.creator_features)
    2. ml_pipeline.py must have been trained
       (saves model files to ./models/)

  OUTPUT FORMAT:
    ╔══════════════════════════════════════════╗
    ║  @cristiano  —  MEGA  ║  ₹19.24 Cr      ║
    ╚══════════════════════════════════════════╝
    Full breakdown: tier, price, risk, score, grade, market range
================================================================================
"""

import os, sys, json
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from pymongo import MongoClient

# ============================================================================
#  CONFIG  — must match ml_pipeline.py
# ============================================================================
## vinay's changes

MONGO_URI = os.getenv("MONGO_URI" ,"mongodb+srv://admin:colabmind2026@colabmind.ueixusq.mongodb.net/?appName=ColabMind")
DB_NAME             = "instagram_db"
FEATURES_COLLECTION = "creator_features"
MODELS_DIR          = Path("./models")
USD_TO_INR          = float(os.getenv("USD_TO_INR", "83.5"))

PRICE_FEATURES = [
    "followers_log", "follower_following_ratio",
    "engagement_rate_avg", "engagement_cv",
    "avg_likes", "avg_comments", "avg_views",
    "posting_frequency_weekly", "video_ratio", "image_ratio",
    "avg_hashtag_count", "avg_caption_length", "avg_mention_count",
    "collab_post_ratio", "affiliate_link_ratio",
    "brand_mentions_per_post", "avg_brand_keyword_score",
    "authority_score", "content_quality_score",
    "engagement_consistency_score",
    "topic_fitness", "topic_travel", "topic_food", "topic_fashion",
    "topic_tech", "topic_comedy", "topic_sports", "topic_lifestyle",
]

RISK_FEATURES = [
    "followers_log", "engagement_rate_avg",
    "controversial_keyword_score", "political_content_ratio",
    "sensitive_topic_ratio", "toxicity_score",
    "collab_post_ratio", "avg_hashtag_count",
    "topic_fitness", "topic_travel", "topic_food", "topic_fashion",
    "topic_tech", "topic_comedy", "topic_sports", "topic_lifestyle",
]


# ============================================================================
#  HELPERS
# ============================================================================

def format_inr(amount: float) -> str:
    if amount >= 1_00_00_000: return f"₹{amount / 1_00_00_000:.2f} Cr"
    if amount >= 1_00_000:    return f"₹{amount / 1_00_000:.2f} L"
    if amount >= 1_000:       return f"₹{amount / 1_000:.2f} K"
    return f"₹{amount:.0f}"


def score_grade(score: float) -> str:
    if score >= 85: return "S  ★★★★★  Elite"
    if score >= 70: return "A  ★★★★☆  Strong"
    if score >= 55: return "B  ★★★☆☆  Good"
    if score >= 40: return "C  ★★☆☆☆  Average"
    return              "D  ★☆☆☆☆  Weak"


def tier_market_range(tier: str) -> tuple:
    return {
        "nano":  (500,       5_000),
        "micro": (5_000,     50_000),
        "mid":   (50_000,    3_00_000),
        "macro": (3_00_000,  15_00_000),
        "mega":  (15_00_000, 5_00_00_000),
    }.get(tier, (500, 5_000))


def positioning(tier: str, price_inr: float) -> str:
    lo, hi = tier_market_range(tier)
    if lo <= price_inr <= hi: return "✔  Within market range"
    if price_inr > hi:        return "↑  Above market range (premium)"
    return                           "↓  Below market range"


def risk_emoji(label: str) -> str:
    return {"LOW": "🟢 LOW", "MEDIUM": "🟡 MEDIUM", "HIGH": "🔴 HIGH"}.get(label, label)


# ============================================================================
#  ATLAS FETCH
# ============================================================================

def fetch_feature_vector(username: str) -> dict:
    """
    Fetch the pre-computed feature vector from creator_features collection.
    Returns the full document dict or raises ValueError if not found.
    """
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=8000)
    client.admin.command("ping")
    db  = client[DB_NAME]
    doc = db[FEATURES_COLLECTION].find_one(
        {"username": username, "influencer_valid": True},
        {"_id": 0}
    )
    client.close()

    if not doc:
        # Try without influencer_valid filter to give a helpful message
        client2 = MongoClient(MONGO_URI, serverSelectionTimeoutMS=8000)
        any_doc = client2[DB_NAME][FEATURES_COLLECTION].find_one(
            {"username": username}, {"_id": 0, "influencer_valid": 1, "influencer_tier": 1}
        )
        client2.close()

        if any_doc:
            raise ValueError(
                f"@{username} exists but is marked as NON_INFLUENCER "
                f"(followers < 1000 or follower/following ratio < 2). "
                f"Not eligible for collaboration pricing."
            )
        raise ValueError(
            f"@{username} not found in creator_features.\n"
            f"  → Run atlas_pipeline_runner.py first to extract features."
        )

    if not doc.get("feature_vector"):
        raise ValueError(
            f"@{username} has no feature_vector. "
            f"Re-run atlas_pipeline_runner.py to rebuild."
        )

    return doc


# ============================================================================
#  MODEL LOADER
# ============================================================================

def load_models() -> dict:
    """Load all saved model files from ./models/."""
    required = [
        "price_model.joblib", "price_scaler.joblib",
        "risk_model.joblib",  "risk_encoder.joblib",
        "scorer_model.joblib", "training_report.json",
    ]
    missing = [f for f in required if not (MODELS_DIR / f).exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing model files: {missing}\n"
            f"  → Run: python ml_pipeline.py  (or  python ml_pipeline.py --synthetic)"
        )

    with open(MODELS_DIR / "training_report.json") as f:
        report = json.load(f)

    return {
        "price_model":   joblib.load(MODELS_DIR / "price_model.joblib"),
        "price_scaler":  joblib.load(MODELS_DIR / "price_scaler.joblib"),
        "risk_model":    joblib.load(MODELS_DIR / "risk_model.joblib"),
        "risk_encoder":  joblib.load(MODELS_DIR / "risk_encoder.joblib"),
        "scorer_model":  joblib.load(MODELS_DIR / "scorer_model.joblib"),
        "scorer_features": report["scorer_model"]["features"],
        "report":          report,
    }


# ============================================================================
#  PREDICTION CORE
# ============================================================================

def predict_from_doc(doc: dict, models: dict) -> dict:
    """
    Run all 3 predictions given a creator_features document and loaded models.
    All model inputs are pandas DataFrames — no raw numpy.
    Returns a structured result dict.
    """
    fv = doc["feature_vector"]

    # ── Build input DataFrames (single-row, named columns)
    price_df  = pd.DataFrame([{col: float(fv.get(col, 0.0)) for col in PRICE_FEATURES}])
    risk_df   = pd.DataFrame([{col: float(fv.get(col, 0.0)) for col in RISK_FEATURES}])
    score_cols = models["scorer_features"]
    scorer_df = pd.DataFrame([{col: float(fv.get(col, 0.0)) for col in score_cols}])

    # ──── MODEL 1: Price Prediction
    price_scaled = pd.DataFrame(
        models["price_scaler"].transform(price_df),
        columns=PRICE_FEATURES,
    )
    price_log = float(models["price_model"].predict(price_scaled)[0])
    price_inr = float(np.expm1(price_log)) / 4
    price_usd = price_inr / USD_TO_INR 

    # ──── MODEL 2: Brand Risk
    risk_encoded = int(models["risk_model"].predict(risk_df)[0])
    risk_label   = models["risk_encoder"].inverse_transform([risk_encoded])[0]
    risk_proba_arr = models["risk_model"].predict_proba(risk_df)[0]
    risk_proba = {
        cls: round(float(p), 4)
        for cls, p in zip(models["risk_encoder"].classes_, risk_proba_arr)
    }

    # ──── MODEL 3: Creator Score
    creator_score = float(np.clip(models["scorer_model"].predict(scorer_df)[0], 0, 100))

    # ── Context
    tier  = doc.get("influencer_tier", "nano")
    lo, hi = tier_market_range(tier)

    return {
        "username":       doc.get("username"),
        "tier":           tier,
        "authority":      float(doc.get("authority_score", 0.0)),
        "topic":          doc.get("dominant_topic", "lifestyle"),
        "followers":      int(fv.get("follower_count", 0)),
        "engagement_rate": float(fv.get("engagement_rate_avg", 0.0)),
        "price_inr":      round(price_inr, 2),
        "price_usd":      round(price_usd, 2),
        "price_fmt":      format_inr(price_inr),
        "market_min":     format_inr(lo),
        "market_max":     format_inr(hi),
        "positioning":    positioning(tier, price_inr),
        "risk_label":     risk_label,
        "risk_proba":     risk_proba,
        "creator_score":  round(creator_score, 2),
        "grade":          score_grade(creator_score),
    }


# ============================================================================
#  OUTPUT PRINTER
# ============================================================================

def print_prediction(r: dict) -> None:
    tier_upper = r["tier"].upper()
    sep  = "═" * 62
    sep2 = "─" * 62

    print(f"\n╔{sep}╗")
    print(f"║  @{r['username']:<20}  {tier_upper:<8}  {r['price_fmt']:>18}  ║")
    print(f"╚{sep}╝")

    print(f"\n  {'Username':<28}: @{r['username']}")
    print(f"  {'Tier':<28}: {tier_upper}")
    print(f"  {'Followers':<28}: {r['followers']:,}")
    print(f"  {'Avg Engagement Rate':<28}: {r['engagement_rate'] * 100:.3f}%")
    print(f"  {'Authority Score':<28}: {r['authority']:.1f} / 100")
    print(f"  {'Content Topic':<28}: {r['topic'].title()}")

    print(f"\n  {sep2}")
    print(f"  COLLABORATION PRICE ESTIMATE")
    print(f"  {sep2}")
    print(f"  {'Price per Post (INR)':<28}: {r['price_fmt']}  (₹{r['price_inr']:,.2f})")
    print(f"  {'Price per Post (USD)':<28}: ${r['price_usd']:,.2f}")
    print(f"  {'Market Range (INR)':<28}: {r['market_min']} – {r['market_max']}")
    print(f"  {'Market Positioning':<28}: {r['positioning']}")

    print(f"\n  {sep2}")
    print(f"  BRAND RISK ASSESSMENT")
    print(f"  {sep2}")
    print(f"  {'Risk Category':<28}: {risk_emoji(r['risk_label'])}")
    print(f"  {'Probabilities':<28}:")
    for cls, prob in sorted(r["risk_proba"].items()):
        bar = "█" * int(prob * 30)
        print(f"      {cls:<8}: {prob:.2%}  {bar}")

    print(f"\n  {sep2}")
    print(f"  CREATOR PERFORMANCE")
    print(f"  {sep2}")
    print(f"  {'Creator Score':<28}: {r['creator_score']:.1f} / 100")
    print(f"  {'Grade':<28}: {r['grade']}")

    print(f"\n  {sep2}")
    print(f"  PRICING TIERS REFERENCE  (Indian Market)")
    print(f"  {sep2}")
    tiers = [
        ("Nano  (1K–10K)",    "₹500",    "₹5 K"),
        ("Micro (10K–100K)",  "₹5 K",    "₹50 K"),
        ("Mid   (100K–1M)",   "₹50 K",   "₹3 L"),
        ("Macro (1M–10M)",    "₹3 L",    "₹15 L"),
        ("Mega  (10M+)",      "₹15 L",   "₹5 Cr"),
    ]
    for label, lo, hi in tiers:
        marker = "  ◀ YOU" if label.lower().startswith(r["tier"]) else ""
        print(f"    {label:<22}  {lo:>8}  –  {hi:<10}{marker}")
    print()


# ============================================================================
#  MAIN PREDICT FUNCTION  (importable)
# ============================================================================

def predict(username: str, verbose: bool = True) -> dict:
    """
    Main entry point.  Accepts an Instagram username string.
    Fetches feature vector from Atlas, runs all 3 models, returns result dict.

    Args:
        username : Instagram handle (with or without @)
        verbose  : if True, prints full formatted output

    Returns:
        dict with keys: price_inr, price_usd, price_fmt, risk_label,
                        creator_score, grade, tier, positioning, ...
    """
    # Strip leading @
    username = username.lstrip("@").strip().lower()

    if verbose:
        print(f"\n[→] Fetching @{username} from Atlas...")

    # ── Fetch
    doc = fetch_feature_vector(username)

    # ── Load models
    if verbose:
        print(f"[→] Running predictions...")
    models = load_models()

    # ── Predict
    result = predict_from_doc(doc, models)

    # ── Print
    if verbose:
        print_prediction(result)

    return result


# ============================================================================
#  BATCH PREDICT  (all influencers in creator_features)
# ============================================================================

def predict_all(limit: int = 0, verbose: bool = True) -> list:
    """
    Run predictions on all valid influencers in creator_features.
    Returns a list of result dicts sorted by price_inr descending.
    """
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=8000)
    client.admin.command("ping")
    db = client[DB_NAME]
    query = db[FEATURES_COLLECTION].find(
        {"influencer_valid": True, "feature_vector": {"$exists": True}},
        {"_id": 0}
    )
    if limit > 0:
        query = query.limit(limit)
    docs = list(query)
    client.close()

    if not docs:
        print("[!] No valid influencer documents found.")
        return []

    models  = load_models()
    results = []

    print(f"\n[→] Predicting {len(docs)} influencers...\n")
    print(f"  {'Username':<25}  {'Tier':<7}  {'Price (INR)':>14}  {'Risk':<8}  {'Score':>6}")
    print("  " + "─" * 65)

    for doc in docs:
        try:
            r = predict_from_doc(doc, models)
            results.append(r)
            if verbose:
                print(
                    f"  @{r['username']:<24}  {r['tier']:<7}"
                    f"  {r['price_fmt']:>14}  {r['risk_label']:<8}"
                    f"  {r['creator_score']:>5.1f}"
                )
        except Exception as e:
            print(f"  [ERROR] {doc.get('username', '?')}: {e}")

    results.sort(key=lambda x: x["price_inr"], reverse=True)
    print(f"\n  Total predicted : {len(results)}")
    print(f"  Highest price   : {results[0]['price_fmt']} (@{results[0]['username']})")
    print(f"  Lowest price    : {results[-1]['price_fmt']} (@{results[-1]['username']})")
    return results


# ============================================================================
#  ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        # Interactive mode
        print("╔════════════════════════════════════════╗")
        print("║   Influencer Collaboration Predictor   ║")
        print("╚════════════════════════════════════════╝")
        username = input("\n  Enter Instagram username: ").strip()
        if username:
            try:
                predict(username)
            except (ValueError, FileNotFoundError) as e:
                print(f"\n[!] {e}")

    elif args[0] == "--all":
        limit = int(args[1]) if len(args) > 1 else 0
        try:
            predict_all(limit=limit)
        except (ValueError, FileNotFoundError) as e:
            print(f"\n[!] {e}")

    else:
        username = args[0]
        try:
            predict(username)
        except (ValueError, FileNotFoundError) as e:
            print(f"\n[!] {e}")