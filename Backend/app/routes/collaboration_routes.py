from flask import Blueprint, request
from bson import ObjectId
from datetime import datetime

from app.config import Config
from app.models.collaboration import CollaborationModel
from app.utils.db import get_collection
from app.utils.helpers import (
    serialize_doc,
    serialize_list,
    success_response,
    error_response,
    now_iso
)
from app.utils.validators import is_valid_object_id, validate_required_fields
from app.utils.auth import get_current_brand


collaboration_bp = Blueprint("collaboration", __name__)

COL = Config.COLLECTION_COLLABORATIONS
C_COL = Config.COLLECTION_CREATORS


# CREATE COLLABORATION
@collaboration_bp.route("/create", methods=["POST"])
def create_collaboration():

    brand_id, err = get_current_brand()
    if err:
        return err

    data = request.get_json() or {}

    missing = validate_required_fields(data, ["creator_id", "agreed_price"])
    if missing:
        return error_response(f"Missing fields: {', '.join(missing)}")

    creator_id = str(data.get("creator_id")).strip()

    if not is_valid_object_id(creator_id):
        return error_response("Invalid creator_id.")

    creators_collection = get_collection(C_COL)

    creator = creators_collection.find_one({
        "_id": ObjectId(creator_id)
    })

    if not creator:
        return error_response("Creator not found.", 404)

    # IMPORTANT PART
    data["creator_id"] = creator_id
    data["brand_id"] = str(brand_id)

    doc = CollaborationModel.new(data)

    result = get_collection(COL).insert_one(doc)

    doc["_id"] = str(result.inserted_id)

    creators_collection.update_one(
        {"_id": ObjectId(creator_id)},
        {"$inc": {"total_collaborations": 1}}
    )

    return success_response(doc, "Collaboration created.", 201)

# LIST COLLABORATIONS
@collaboration_bp.route("/list", methods=["GET"])
def list_collaborations():

    brand_id, err = get_current_brand()
    if err:
        return err

    col = get_collection(COL)

    query = {
        "brand_id": brand_id
    }

    creator_id = request.args.get("creator_id")

    if creator_id:

        if not is_valid_object_id(creator_id):
            return error_response("Invalid creator ID.")

        query["creator_id"] = creator_id

    docs = list(
        col.find(query).sort("created_at", -1)
    )

    return success_response(serialize_list(docs))


# GET SINGLE COLLABORATION
@collaboration_bp.route("/<collab_id>", methods=["GET"])
def get_collaboration(collab_id):

    brand_id, err = get_current_brand()
    if err:
        return err

    if not is_valid_object_id(collab_id):
        return error_response("Invalid collaboration ID.")

    doc = get_collection(COL).find_one({
        "_id": ObjectId(collab_id),
        "brand_id": brand_id
    })

    if not doc:
        return error_response("Collaboration not found.", 404)

    return success_response(serialize_doc(doc))


# UPDATE COLLABORATION
@collaboration_bp.route("/update/<collab_id>", methods=["PUT"])
def update_collaboration(collab_id):

    brand_id, err = get_current_brand()
    if err:
        return err

    if not is_valid_object_id(collab_id):
        return error_response("Invalid collaboration ID.")

    data = request.get_json() or {}

    col = get_collection(COL)

    doc = col.find_one({
        "_id": ObjectId(collab_id),
        "brand_id": brand_id
    })

    if not doc:
        return error_response("Collaboration not found.", 404)

    # UPDATE STATUS
    if "status" in data:
        try:
            col.update_one(
                {"_id": ObjectId(collab_id)},
                CollaborationModel.update_status(data["status"])
            )
        except ValueError as e:
            return error_response(str(e))

    # RECORD PAYMENT
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
                    ).days
                )

            except:
                delay_days = 0

        col.update_one(
            {"_id": ObjectId(collab_id)},
            CollaborationModel.record_payment(received_on, delay_days)
        )

    updated = col.find_one({
        "_id": ObjectId(collab_id)
    })

    return success_response(
        serialize_doc(updated),
        "Collaboration updated."
    )


# DELETE COLLABORATION
@collaboration_bp.route("/<collab_id>", methods=["DELETE"])
def delete_collaboration(collab_id):

    brand_id, err = get_current_brand()
    if err:
        return err

    if not is_valid_object_id(collab_id):
        return error_response("Invalid collaboration ID.")

    result = get_collection(COL).delete_one({
        "_id": ObjectId(collab_id),
        "brand_id": brand_id
    })

    if result.deleted_count == 0:
        return error_response("Collaboration not found.", 404)

    return success_response(
        message="Collaboration deleted."
    )