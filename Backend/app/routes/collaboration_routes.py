from flask import Blueprint, request
from bson import ObjectId
from datetime import datetime

from app.config import Config
from app.models.collaboration import CollaborationModel
from app.utils.db import get_collection
from app.utils.helpers import serialize_doc, serialize_list, success_response, error_response, now_iso
from app.utils.validators import is_valid_object_id, validate_required_fields

collaboration_bp = Blueprint("collaboration", __name__)

COL = Config.COLLECTION_COLLABORATIONS
C_COL = Config.COLLECTION_CREATORS


# CREATE COLLABORATION
@collaboration_bp.route("/create", methods=["POST"])
def create_collaboration():

    data = request.get_json() or {}

    missing = validate_required_fields(data, ["creator_id", "agreed_price"])
    if missing:
        return error_response(f"Missing fields: {', '.join(missing)}")

    if not is_valid_object_id(data["creator_id"]):
        return error_response("Invalid creator_id.")

    if not get_collection(C_COL).find_one({"_id": ObjectId(data["creator_id"])}):
        return error_response("Creator not found.", 404)

    doc = CollaborationModel.new(data)

    result = get_collection(COL).insert_one(doc)
    doc["_id"] = str(result.inserted_id)

    get_collection(C_COL).update_one(
        {"_id": ObjectId(data["creator_id"])},
        {"$inc": {"total_collaborations": 1}}
    )

    return success_response(doc, "Collaboration created.", 201)


# LIST COLLABORATIONS
@collaboration_bp.route("/list/<creator_id>", methods=["GET"])
def list_collaborations(creator_id):

    if not is_valid_object_id(creator_id):
        return error_response("Invalid creator ID.")

    docs = list(
        get_collection(COL)
        .find({"creator_id": creator_id})
        .sort("created_at", -1)
    )

    return success_response(serialize_list(docs))


# GET SINGLE COLLABORATION
@collaboration_bp.route("/<collab_id>", methods=["GET"])
def get_collaboration(collab_id):

    if not is_valid_object_id(collab_id):
        return error_response("Invalid collaboration ID.")

    doc = get_collection(COL).find_one({"_id": ObjectId(collab_id)})

    if not doc:
        return error_response("Collaboration not found.", 404)

    return success_response(serialize_doc(doc))


# UPDATE COLLABORATION
@collaboration_bp.route("/update/<collab_id>", methods=["PUT"])
def update_collaboration(collab_id):

    if not is_valid_object_id(collab_id):
        return error_response("Invalid collaboration ID.")

    data = request.get_json() or {}
    col = get_collection(COL)

    doc = col.find_one({"_id": ObjectId(collab_id)})

    if not doc:
        return error_response("Collaboration not found.", 404)

    # STATUS UPDATE
    if "status" in data:
        try:
            col.update_one(
                {"_id": ObjectId(collab_id)},
                CollaborationModel.update_status(data["status"])
            )
        except ValueError as e:
            return error_response(str(e))

    # PAYMENT UPDATE
    if data.get("payment_status") == "paid":

        received_on = data.get("payment_received_on", now_iso())

        delay_days = 0

        deadline = doc.get("deadline")

        if deadline:
            try:
                delay_days = max(
                    0,
                    (
                        datetime.fromisoformat(received_on)
                        - datetime.fromisoformat(deadline)
                    ).days,
                )
            except:
                delay_days = 0

        col.update_one(
            {"_id": ObjectId(collab_id)},
            CollaborationModel.record_payment(received_on, delay_days)
        )

    # POST PERFORMANCE
    if any(k in data for k in ("post_likes", "post_comments", "post_views")):

        col.update_one(
            {"_id": ObjectId(collab_id)},
            CollaborationModel.update_performance(
                data.get("post_likes", 0),
                data.get("post_comments", 0),
                data.get("post_views", 0),
                data.get("post_url", "")
            )
        )

    updated = serialize_doc(col.find_one({"_id": ObjectId(collab_id)}))

    return success_response(updated, "Collaboration updated.")


# DELETE
@collaboration_bp.route("/<collab_id>", methods=["DELETE"])
def delete_collaboration(collab_id):

    if not is_valid_object_id(collab_id):
        return error_response("Invalid collaboration ID.")

    result = get_collection(COL).delete_one({"_id": ObjectId(collab_id)})

    if result.deleted_count == 0:
        return error_response("Collaboration not found.", 404)

    return success_response(message="Collaboration deleted.")