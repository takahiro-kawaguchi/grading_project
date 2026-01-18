from flask import Blueprint, render_template, current_app
from grader_app.utils import refresh_app_config
from flask import redirect, request, url_for


main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template("index.html")

@main_bp.route('/reload_reports/')
def reload_reports():
    """PDFとCodeのリストを再読み込みするルート"""
    refresh_app_config()
    return redirect(request.referrer or url_for('main.index'))