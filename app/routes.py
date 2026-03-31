from flask import Blueprint, jsonify

bp = Blueprint("main", __name__)


@bp.get("/health")
def health():
    return jsonify({"status": "ok"})
