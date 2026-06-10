"""Web application package."""

from flask import Flask

from .routes import bp


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = app.config.get("SECRET_KEY") or "dev"
    app.register_blueprint(bp)
    return app
