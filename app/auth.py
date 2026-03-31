import functools
import hmac

from flask import abort, current_app, request


def require_api_key(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get("X-API-Key", "")
        expected = current_app.config["API_KEY"]
        if not api_key or not hmac.compare_digest(api_key, expected):
            abort(401, description="Invalid or missing API key")
        return f(*args, **kwargs)

    return decorated
