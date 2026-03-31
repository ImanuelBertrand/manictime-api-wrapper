import logging
import os

import httpx
from flask import Flask, jsonify
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from .mt_client import ManicTimeAPIError, ManicTimeClient

cache = Cache()
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
    app.config["MT_SERVER_URL"] = os.environ["MT_SERVER_URL"]
    app.config["MT_USERNAME"] = os.environ["MT_USERNAME"]
    app.config["MT_PASSWORD"] = os.environ["MT_PASSWORD"]
    app.config["API_KEY"] = os.environ["API_KEY"]

    app.config["CACHE_TYPE"] = "SimpleCache"
    app.config["CACHE_DEFAULT_TIMEOUT"] = int(
        os.environ.get("CACHE_DEFAULT_TIMEOUT", 300)
    )

    app.config["RATELIMIT_STORAGE_URI"] = os.environ.get(
        "RATELIMIT_STORAGE_URI", "memory://"
    )

    cache.init_app(app)
    limiter.init_app(app)

    app.extensions["mt_client"] = ManicTimeClient(
        server_url=app.config["MT_SERVER_URL"],
        username=app.config["MT_USERNAME"],
        password=app.config["MT_PASSWORD"],
    )

    logger = logging.getLogger(__name__)

    @app.errorhandler(ManicTimeAPIError)
    def handle_mt_error(error):
        logger.warning("ManicTime API error %d: %s", error.status_code, error.detail)
        return jsonify({"error": "Upstream request failed"}), error.status_code

    @app.errorhandler(httpx.HTTPError)
    def handle_http_error(_error):
        logger.warning("Upstream connection error: %s", _error)
        return jsonify({"error": "Upstream connection failed"}), 502

    from .routes import bp  # noqa: PLC0415

    app.register_blueprint(bp)

    return app
