import re
from datetime import datetime
from pathlib import Path

from flask import Blueprint, Response, abort, current_app, jsonify, request

from . import cache
from .auth import require_api_key

TIMELINE_KEY_PATTERN = re.compile(r"^[\w-]{1,128}$")


def _validate_iso_datetime(value: str, name: str) -> None:
    try:
        datetime.fromisoformat(value)
    except ValueError:
        abort(400, description=f"{name} must be a valid ISO 8601 date or datetime")


bp = Blueprint("main", __name__)


@bp.get("/health")
def health():
    if request.args.get("deep", "").lower() == "true":
        client = current_app.extensions["mt_client"]
        mt_ok = client.check_health()
        status = "ok" if mt_ok else "degraded"
        return jsonify({"status": status, "manictime": mt_ok}), 200 if mt_ok else 503
    return jsonify({"status": "ok"})


@bp.get("/api/openapi.yaml")
def openapi_spec():
    spec_path = Path(__file__).parent / "openapi.yaml"
    return Response(spec_path.read_text(), mimetype="text/yaml")


@bp.get("/api/timelines")
@require_api_key
@cache.cached()
def timelines():
    client = current_app.extensions["mt_client"]
    return jsonify(client.get_timelines())


@bp.get("/api/timelines/<timeline_key>/activities")
@require_api_key
@cache.cached(query_string=True)
def activities(timeline_key: str):
    if not TIMELINE_KEY_PATTERN.match(timeline_key):
        abort(400, description="Invalid timeline key")
    from_time = request.args.get("fromTime")
    to_time = request.args.get("toTime")
    if not from_time or not to_time:
        abort(400, description="fromTime and toTime query parameters are required")
    _validate_iso_datetime(from_time, "fromTime")
    _validate_iso_datetime(to_time, "toTime")
    client = current_app.extensions["mt_client"]
    return jsonify(client.get_activities(timeline_key, from_time, to_time))


@bp.get("/api/tags")
@require_api_key
@cache.cached(query_string=True)
def tags():
    get_all = request.args.get("all", "").lower() == "true"
    client = current_app.extensions["mt_client"]
    return jsonify(client.get_tag_combinations(get_all=get_all))


@bp.get("/api/screenshots")
@require_api_key
@cache.cached()
def screenshots():
    client = current_app.extensions["mt_client"]
    return jsonify(client.get_screenshots())
