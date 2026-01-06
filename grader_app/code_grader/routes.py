from flask import Blueprint, render_template, current_app

code_bp = Blueprint(
    'code', __name__, 
    template_folder='templates', 
    static_folder='static',
    url_prefix='/code'
)

@code_bp.route('/')
def index():
    sorted_dirlist = current_app.config['CODE_LIST']
    finished = [False for report in sorted_dirlist]
    return render_template("dirlist.html", dirlist=sorted_dirlist, finished=finished)
