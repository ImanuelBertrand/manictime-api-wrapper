import os

import httpx
from flask import Flask, jsonify
from flask_caching import Cache

from .mt_client import ManicTimeAPIError, ManicTimeClient

cache = Cache()


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

    cache.init_app(app)

    app.extensions["mt_client"] = ManicTimeClient(
        server_url=app.config["MT_SERVER_URL"],
        username=app.config["MT_USERNAME"],
        password=app.config["MT_PASSWORD"],
    )

    @app.errorhandler(ManicTimeAPIError)
    def handle_mt_error(error):
        return jsonify({"error": error.detail}), error.status_code

    @app.errorhandler(httpx.HTTPError)
    def handle_http_error(_error):
        return jsonify({"error": "Upstream connection failed"}), 502

    from .routes import bp  # noqa: PLC0415

    app.register_blueprint(bp)

    return app
