import os
from flask import Flask
from flask_caching import Cache

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

    from .routes import bp

    app.register_blueprint(bp)

    return app
