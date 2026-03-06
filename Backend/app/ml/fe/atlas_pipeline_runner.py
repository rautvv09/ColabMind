"""
================================================================================
  MongoDB Atlas → Feature Engineering Pipeline
  Cluster  : instagram_db
  Collections: profiles, brand_collabs
================================================================================

  SETUP:
    pip install pymongo[srv] dnspython

  USAGE:
    # Set your Atlas connection string once:
    export MONGO_URI="mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority"

    # Then run:
    python atlas_pipeline_runner.py

================================================================================
"""

import os
import json
import math
import pprint
from datetime import datetime
from typing import Optional, Iterator

# ── pymongo (required) ───────────────────────────────────────────────────────
try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, OperationFailure
except ImportError:
    raise SystemExit(
        "\n[ERROR] pymongo not installed.\n"
        "Run: pip install 'pymongo[srv]' dnspython\n"
    )

# ── local pipeline (must be in same directory or PYTHONPATH) ─────────────────
from feature_engineering_pipeline import (
    run_pipeline,
    CreatorPerformanceScorer,
    clean_document,
    extract_post_features,
    aggregate_profile_features,
    compute_temporal_features,
    compute_audience_features,
    compute_topic_vector,
    compute_collaboration_features,
    compute_authority_features,
    compute_brand_risk_features,
    build_feature_vector,
    apply_eligibility_filter,
    _safe_int,
    _safe_float,
    classify_influencer_tier,
)


# ============================================================================
#  CONFIG — edit or set via environment variables
# ============================================================================

MONGO_URI  = os.getenv(
    "MONGO_URI",
    "mongodb+srv://admin:colabmind2026@colabmind.ueixusq.mongodb.net/?appName=ColabMind"
)

DB_NAME             = "instagram_db"
PROFILES_COLLECTION = "profiles"
COLLABS_COLLECTION  = "brand_collabs"
OUTPUT_COLLECTION   = "creator_features"   # where enriched vectors are written back

BATCH_SIZE          = 50    # how many profiles to fetch per cursor batch


# ============================================================================
#  ATLAS CONNECTION
# ============================================================================

def get_client(uri: str = MONGO_URI) -> MongoClient:
    """
    Create a MongoClient connected to Atlas.
    Uses SRV connection string (mongodb+srv://...).
    """
    client = MongoClient(
        uri,
        serverSelectionTimeoutMS=8000,
        connectTimeoutMS=8000,
        socketTimeoutMS=30000,
    )
    # Verify connection is alive
    client.admin.command("ping")
    print(f"[✓] Connected to Atlas  →  {DB_NAME}")
    return client


# ============================================================================
#  FETCH HELPERS
# ============================================================================

def fetch_profiles(
    db,
    filter_query: dict = None,
    limit: int = 0,
    skip: int = 0,
) -> Iterator[dict]:
    """
    Stream documents from the `profiles` collection.

    Default filter: only eligible influencers (pre-filter in MongoDB for speed).
      follower_count          >= 1000
      follower_following_ratio >= 2

    Args:
        filter_query : override the default MongoDB filter
        limit        : 0 = fetch all
        skip         : pagination offset
    """
    default_filter = {
        "profile.follower_count":           {"$gte": 1000},
        "profile.follower_following_ratio": {"$gte": 2},
    }
    query  = filter_query if filter_query is not None else default_filter
    cursor = db[PROFILES_COLLECTION].find(
        query,
        batch_size=BATCH_SIZE,
        skip=skip,
    )
    if limit > 0:
        cursor = cursor.limit(limit)
    return cursor


def fetch_brand_collabs(db, username: str) -> list:
    """
    Fetch brand_collab documents for a specific influencer username.
    Collection: brand_collabs
    Example document key: { influencer_username: "zakirkhan_208", ... }
    """
    return list(
        db[COLLABS_COLLECTION].find(
            {"influencer_username": username},
            {"_id": 0}
        )
    )


def fetch_single_profile(db, username: str) -> Optional[dict]:
    """Fetch one profile document by username."""
    return db[PROFILES_COLLECTION].find_one(
        {"profile.username": username},
        {"_id": 0}
    )


def enrich_profile_with_collabs(profile_doc: dict, collab_docs: list) -> dict:
    """
    Merge brand_collab data into the profile document so the pipeline
    has full collaboration context.

    Adds / overwrites:
        doc['brand_summary']      ← from brand_collabs collection
        doc['total_collabs']
        doc['collab_type_breakdown']
        doc['total_estimated_value_usd']
    """
    if not collab_docs:
        return profile_doc

    # Use the first collab document (they are per-influencer)
    collab = collab_docs[0]
    profile_doc["brand_summary"]           = collab.get("brand_summary", [])
    profile_doc["total_collabs"]           = collab.get("total_collabs", 0)
    profile_doc["collab_type_breakdown"]   = collab.get("collab_type_breakdown", {})
    profile_doc["total_estimated_value_usd"] = collab.get("total_estimated_value_usd", 0)

    # If brand_collabs has richer post-level data, inject into posts list
    collab_posts = collab.get("collab_posts", [])
    existing_ids = {p.get("post_id") for p in profile_doc.get("posts", [])}
    for cp in collab_posts:
        if cp.get("post_id") not in existing_ids:
            profile_doc.setdefault("posts", []).append(cp)

    return profile_doc


# ============================================================================
#  WRITE BACK — store enriched feature vectors to creator_features collection
# ============================================================================

def write_feature_vector(db, pipeline_output: dict) -> None:
    """
    Upsert the feature vector output into the `creator_features` collection.
    """
    username = pipeline_output.get("username")
    if not username:
        return

    doc = {
        "username":             username,
        "influencer_valid":     pipeline_output.get("influencer_valid"),
        "influencer_tier":      pipeline_output.get("influencer_tier"),
        "creator_type":         pipeline_output.get("creator_type"),
        "paid_collab_eligible": pipeline_output.get("paid_collab_eligible"),
        "feature_vector":       pipeline_output.get("feature_vector"),
        "feature_dim":          pipeline_output.get("feature_dim"),
        # Key derived outputs surfaced at top level for easy querying
        "authority_score": (
            pipeline_output.get("stages", {})
            .get("authority", {})
            .get("authority_score", 0.0)
        ),
        "brand_risk_category": (
            pipeline_output.get("stages", {})
            .get("brand_risk", {})
            .get("brand_risk_category", "UNKNOWN")
        ),
        "dominant_topic": (
            pipeline_output.get("stages", {})
            .get("topic_vector", {})
            .get("dominant_topic", "lifestyle")
        ),
        "last_updated": datetime.utcnow(),
    }

    # Attach creator score
    if pipeline_output.get("feature_vector"):
        scorer = CreatorPerformanceScorer()
        doc["creator_score"] = scorer.score(pipeline_output["feature_vector"])

    db[OUTPUT_COLLECTION].update_one(
        {"username": username},
        {"$set": doc},
        upsert=True,
    )


# ============================================================================
#  BATCH PIPELINE RUNNER
# ============================================================================

def run_batch_pipeline(
    limit: int = 0,
    skip: int = 0,
    write_back: bool = True,
    verbose: bool = True,
) -> list:
    """
    Full batch runner:
      1. Connect to Atlas
      2. Fetch profiles (with pre-filter)
      3. Join with brand_collabs per influencer
      4. Run feature engineering pipeline on each
      5. Optionally write results back to creator_features
      6. Return list of pipeline outputs

    Args:
        limit      : max profiles to process (0 = all)
        skip       : pagination offset
        write_back : if True, upsert enriched vectors to creator_features
        verbose    : print per-profile summary
    """
    client = get_client()
    db     = client[DB_NAME]

    results   = []
    processed = 0
    skipped   = 0
    errors    = 0

    print(f"\n[→] Fetching from  '{DB_NAME}.{PROFILES_COLLECTION}'  ...")
    cursor = fetch_profiles(db, limit=limit, skip=skip)

    for raw_doc in cursor:
        # Remove MongoDB internal _id for clean processing
        raw_doc.pop("_id", None)

        username = raw_doc.get("profile", {}).get("username", "unknown")

        try:
            # ── 1. Eligibility pre-check (fast, no heavy processing)
            pre = apply_eligibility_filter(raw_doc.copy())
            if not pre["influencer_valid"]:
                skipped += 1
                if verbose:
                    print(f"  [SKIP]  {username:<25}  → NON_INFLUENCER")
                continue

            # ── 2. Enrich with brand_collabs data
            collab_docs = fetch_brand_collabs(db, username)
            enriched    = enrich_profile_with_collabs(raw_doc, collab_docs)

            # ── 3. Run full feature pipeline
            output = run_pipeline(enriched)

            # ── 4. Write back to creator_features
            if write_back and output["influencer_valid"]:
                write_feature_vector(db, output)

            results.append(output)
            processed += 1

            if verbose:
                fv = output.get("feature_vector") or {}
                print(
                    f"  [OK]    {username:<25}"
                    f"  tier={output['influencer_tier']:<6}"
                    f"  auth={fv.get('authority_score', 0):<6}"
                    f"  risk={output.get('stages', {}).get('brand_risk', {}).get('brand_risk_category', '?'):<7}"
                    f"  dims={output.get('feature_dim', 0)}"
                )

        except Exception as exc:
            errors += 1
            print(f"  [ERROR] {username}  →  {exc}")

    client.close()

    print(f"\n[✓] Done  |  processed={processed}  skipped={skipped}  errors={errors}")
    if write_back:
        print(f"[✓] Feature vectors written to  '{DB_NAME}.{OUTPUT_COLLECTION}'")

    return results


# ============================================================================
#  SINGLE PROFILE RUNNER  (useful for debugging one account)
# ============================================================================

def run_single(username: str, verbose: bool = True) -> Optional[dict]:
    """
    Fetch and run the pipeline for a single username.
    """
    client = get_client()
    db     = client[DB_NAME]

    raw_doc = fetch_single_profile(db, username)
    if not raw_doc:
        print(f"[!] Profile '{username}' not found in '{PROFILES_COLLECTION}'")
        client.close()
        return None

    collab_docs = fetch_brand_collabs(db, username)
    enriched    = enrich_profile_with_collabs(raw_doc, collab_docs)
    output      = run_pipeline(enriched)

    if verbose:
        _print_summary(output)

    client.close()
    return output


# ============================================================================
#  QUERY ENRICHED FEATURES (read from creator_features)
# ============================================================================

def query_top_influencers(
    min_authority: float = 60.0,
    max_risk: str = "LOW",
    tier: str = None,
    limit: int = 20,
) -> list:
    """
    Query the creator_features collection for top influencers.

    Example:
        query_top_influencers(min_authority=70, max_risk='LOW', tier='macro')
    """
    risk_levels = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
    allowed_risks = [k for k, v in risk_levels.items() if v <= risk_levels.get(max_risk, 0)]

    query = {
        "influencer_valid":    True,
        "authority_score":     {"$gte": min_authority},
        "brand_risk_category": {"$in": allowed_risks},
    }
    if tier:
        query["influencer_tier"] = tier

    client = get_client()
    db     = client[DB_NAME]

    docs = list(
        db[OUTPUT_COLLECTION]
        .find(query, {"_id": 0})
        .sort("authority_score", -1)
        .limit(limit)
    )
    client.close()

    print(f"\n[Query] Top {len(docs)} influencers  "
          f"(authority ≥ {min_authority}, risk ≤ {max_risk}"
          + (f", tier={tier}" if tier else "") + ")")
    for d in docs:
        print(
            f"  {d.get('username','?'):<25}"
            f"  tier={d.get('influencer_tier','?'):<6}"
            f"  auth={d.get('authority_score','?'):<6}"
            f"  score={d.get('creator_score','?'):<6}"
            f"  risk={d.get('brand_risk_category','?')}"
        )
    return docs


# ============================================================================
#  PRETTY PRINT HELPER
# ============================================================================

def _print_summary(output: dict) -> None:
    stages = output.get("stages", {})
    fv     = output.get("feature_vector") or {}

    sep = "=" * 62
    print(sep)
    print(f"  USERNAME     : {output.get('username')}")
    print(f"  VALID        : {output.get('influencer_valid')}")
    print(f"  TIER         : {output.get('influencer_tier')}")
    print(f"  CREATOR TYPE : {output.get('creator_type')}")
    print(sep)

    if not output.get("influencer_valid"):
        print(f"  {output.get('message')}")
        print(sep)
        return

    print("  ── Audience")
    a = stages.get("audience", {})
    print(f"     followers      : {a.get('follower_count', 0):,}")
    print(f"     log(followers) : {a.get('follower_count_log')}")
    print(f"     ff_ratio       : {a.get('follower_following_ratio')}")

    print("  ── Engagement")
    ag = stages.get("profile_agg", {})
    print(f"     avg_engagement : {ag.get('avg_engagement_rate')}")
    print(f"     avg_likes      : {ag.get('avg_likes', 0):,}")
    print(f"     avg_comments   : {ag.get('avg_comments', 0):,}")
    print(f"     engagement_cv  : {ag.get('engagement_cv')}")

    print("  ── Temporal")
    t = stages.get("temporal", {})
    print(f"     posts/week     : {t.get('posting_frequency_weekly')}")
    print(f"     consistency    : {t.get('posting_consistency_score')}")

    print("  ── Collaboration")
    c = stages.get("collab", {})
    print(f"     collab_ratio   : {c.get('collab_post_ratio')}")
    print(f"     est. value USD : ${c.get('total_estimated_value_usd', 0):,.2f}")

    print("  ── Authority & Risk")
    auth = stages.get("authority", {})
    risk = stages.get("brand_risk", {})
    print(f"     authority_score: {auth.get('authority_score')}")
    print(f"     risk_category  : {risk.get('brand_risk_category')}")

    print("  ── Topic")
    tv = stages.get("topic_vector", {})
    print(f"     dominant_topic : {tv.get('dominant_topic')}")
    active = [k.replace('topic_','') for k,v in tv.items() if v == 1]
    print(f"     active topics  : {active or ['none detected']}")

    print("  ── Feature Vector")
    print(f"     dimensions     : {output.get('feature_dim')}")

    scorer = CreatorPerformanceScorer()
    print(f"     creator_score  : {scorer.score(fv)}")
    print(sep)


# ============================================================================
#  ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import sys

    # ── Usage examples ────────────────────────────────────────────────────────
    #
    # 1. Run pipeline on ALL eligible profiles → write vectors to creator_features
    #    python atlas_pipeline_runner.py
    #
    # 2. Run on a single account
    #    python atlas_pipeline_runner.py cristiano
    #
    # 3. Run on first N profiles (testing)
    #    python atlas_pipeline_runner.py --limit 10
    # ─────────────────────────────────────────────────────────────────────────

    args = sys.argv[1:]

    if not args:
        # Default: batch run, all eligible profiles
        run_batch_pipeline(write_back=True, verbose=True)

    elif args[0] == "--limit" and len(args) == 2:
        run_batch_pipeline(limit=int(args[1]), write_back=True, verbose=True)

    else:
        # Single account mode
        username = args[0]
        run_single(username, verbose=True)