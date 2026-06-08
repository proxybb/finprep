"""Route definitions for the Flask skeleton."""

from flask import Blueprint, render_template


bp = Blueprint("web", __name__)


@bp.route("/")
def dashboard():
    """Render the dashboard placeholder."""
    return render_template("dashboard.html", active_page="dashboard")


@bp.route("/data")
def data():
    """Render the data intake placeholder."""
    return render_template("data.html", active_page="data")


@bp.route("/data/cleaned")
def cleaned_data():
    """Render the cleaned data preview placeholder."""
    return render_template("cleaned_data.html", active_page="data")


@bp.route("/companies")
def companies():
    """Render the companies placeholder."""
    return render_template("companies.html", active_page="companies")


@bp.route("/analysis")
def analysis():
    """Render the analysis placeholder."""
    return render_template("analysis.html", active_page="analysis")
