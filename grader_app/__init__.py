import os
from flask import Flask
from grader_app.utils import refresh_app_config


def create_app():
    app = Flask(__name__)
    
    # 文字列指定よりも、オブジェクトを直接渡す方が確実です
    from config import Config
    app.config.from_object(Config)

    # フォルダが存在しない場合に自動作成（エラー防止）
    for path in app.config.get('OS_MAKEDIRS', []):
        os.makedirs(path, exist_ok=True)

    with app.app_context():
        refresh_app_config(app)

    # Blueprintの登録（既存の通り）
    from .code_grader.routes import code_bp
    from .pdf_grader.routes import pdf_bp
    app.register_blueprint(code_bp)
    app.register_blueprint(pdf_bp)

    from .main.routes import main_bp
    app.register_blueprint(main_bp)

    return app