import os
from flask import Flask

def create_app():
    app = Flask(__name__)
    
    # 文字列指定よりも、オブジェクトを直接渡す方が確実です
    from config import Config
    app.config.from_object(Config)

    # フォルダが存在しない場合に自動作成（エラー防止）
    for path in app.config.get('OS_MAKEDIRS', []):
        os.makedirs(path, exist_ok=True)

    with app.app_context():
        from grader_app.utils import unzip_if_needed_and_list_folders
        
        # PDFフォルダのスキャン
        pdf_path = app.config['PDF_BASE_DIR']
        raw_pdf_list = unzip_if_needed_and_list_folders(pdf_path)
        from grader_app.pdf_grader.utils import get_report_list
        print("Raw PDF List:", raw_pdf_list)
        pdf_list = get_report_list(raw_pdf_list)
        print("Processed PDF List:", pdf_list)
        app.config['PDF_LIST'] = pdf_list
        app.config['RAW_PDF_LIST'] = raw_pdf_list
        
        # Codeフォルダのスキャン
        code_path = app.config['CODE_BASE_DIR']
        raw_code_list = unzip_if_needed_and_list_folders(code_path)
        from grader_app.code_grader.utils import extract_keys
        app.config['CODE_LIST'] = sorted(raw_code_list, key=extract_keys)

    # Blueprintの登録（既存の通り）
    from .code_grader.routes import code_bp
    from .pdf_grader.routes import pdf_bp
    app.register_blueprint(code_bp)
    app.register_blueprint(pdf_bp)

    from .main.routes import main_bp
    app.register_blueprint(main_bp)

    return app