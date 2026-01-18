import os
import zipfile
from flask import current_app
import json

def unzip_if_needed_and_list_folders(target_dir):
    print(f"Scanning directory: {target_dir}")
    # ディレクトリ内のファイルとフォルダを取得
    for item in os.listdir(target_dir):
        if item.lower().endswith('.zip'):
            zip_path = os.path.join(target_dir, item)
            folder_name = os.path.splitext(item)[0]
            folder_path = os.path.join(target_dir, folder_name)

            # 対応するフォルダがない場合は解凍
            if not os.path.exists(folder_path):
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(folder_path)

    # フォルダ一覧を取得（.zipではないディレクトリ）
    folder_list = [
        name for name in os.listdir(target_dir)
        if os.path.isdir(os.path.join(target_dir, name))
    ]
    
    return folder_list

def refresh_app_config(app=None):
    """PDFとCodeのフォルダをスキャンしてconfigを更新する共通関数"""
    if app is None:
        app = current_app
    
    from grader_app.pdf_grader.utils import get_report_list
    from grader_app.code_grader.utils import extract_keys

    # PDFフォルダのスキャン
    pdf_path = app.config['PDF_BASE_DIR']
    raw_pdf_list = unzip_if_needed_and_list_folders(pdf_path)
    pdf_list = get_report_list(raw_pdf_list)
    
    app.config['PDF_LIST'] = pdf_list
    app.config['RAW_PDF_LIST'] = raw_pdf_list
    
    # Codeフォルダのスキャン
    code_path = app.config['CODE_BASE_DIR']
    raw_code_list = unzip_if_needed_and_list_folders(code_path)
    app.config['CODE_LIST'] = sorted(raw_code_list, key=extract_keys)
    
    print("Config reloaded: PDF and Code lists updated.")

def load_problems_from_json(report_type, report_name):
    dirname = current_app.config[f'{report_type.upper()}_SAVE_DIR']
    DATA_FILE = os.path.join(dirname, f"{report_name}_problems.json")
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    # 初期構造
    return {"order": [], "problems": {}}

def save_problems_to_json(report_type, report_name, data):
    dirname = current_app.config[f'{report_type.upper()}_SAVE_DIR']
    DATA_FILE = os.path.join(dirname, f"{report_name}_problems.json")
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_grades_from_json(report_type, report_name, student_name):
    dirname = os.path.join(current_app.config[f'{report_type.upper()}_SAVE_DIR'], report_name)
    GRADES_FILE = os.path.join(dirname, f"{student_name}.json")
    if os.path.exists(GRADES_FILE):
        with open(GRADES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_grades_to_json(report_type, report_name, student_name, grades):
    dirname = os.path.join(current_app.config[f'{report_type.upper()}_SAVE_DIR'], report_name)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    GRADES_FILE = os.path.join(dirname, f"{student_name}.json")
    with open(GRADES_FILE, 'w', encoding='utf-8') as f:
        json.dump(grades, f, ensure_ascii=False, indent=4)

def check_all_grades_entered(problems, grades):
    for problem_id in problems['order']:
        if f"grade_{problem_id}" not in grades:
            return False
    return True

def find_next_unfinished_student(report_type, report_name, student_names, problems, current_student_index):
    for idx in range(current_student_index + 1, len(student_names)):
        student_name = student_names[idx]
        grades = load_grades_from_json(report_type, report_name, student_name)
        if not check_all_grades_entered(problems, grades):
            return idx, student_name
    for idx in range(0, current_student_index):
        student_name = student_names[idx]
        grades = load_grades_from_json(report_type, report_name, student_name)
        if not check_all_grades_entered(problems, grades):
            return idx, student_name
    return None, None
