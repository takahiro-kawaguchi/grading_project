import os

# config.pyがある場所（プロジェクトのルート）の絶対パスを取得
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # BASE_DIR を基準に結合することで、絶対パスにする
    PDF_BASE_DIR = os.path.join(BASE_DIR, "storage", "pdf")
    PDF_LIST = []
    IMAGE_SUBPATH = "pdf_images"
    IMAGE_DIR = os.path.join(BASE_DIR, "grader_app", "static", IMAGE_SUBPATH)
    PDF_SAVE_DIR = os.path.join(BASE_DIR, "storage", "save", "pdf")

    CODE_BASE_DIR = os.path.join(BASE_DIR, "storage", "code")
    CODE_LIST = []
    CODE_SAVE_DIR = os.path.join(BASE_DIR, "storage", "save", "code")
    
    
    # 必要に応じて、自動でフォルダを作成するための設定
    OS_MAKEDIRS = [PDF_BASE_DIR, CODE_BASE_DIR, IMAGE_DIR, PDF_SAVE_DIR, CODE_SAVE_DIR]