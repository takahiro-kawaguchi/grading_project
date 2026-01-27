import os
import zipfile
from flask import current_app
import json
import glob

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


def get_enrolled_students(report_type):
    dirname = current_app.config[f'{report_type.upper()}_BASE_DIR']
    print(f"Looking for enrolled student files in directory: {dirname}")
    
    # .xls と .xlsx 両方に対応できるようにしておくとより安全です
    target_files = glob.glob(os.path.join(dirname, "*seiseki*.xls*"))
    
    print(f"Enrolled student files found: {target_files}")
    if not target_files:
        print("エラー: 'seiseki' を含むファイルが見つかりませんでした。")
        return None
    if len(target_files) > 1:
        print("エラー: 'seiseki' を含むファイルが複数見つかりました。")
        return None
        
    target_file = target_files[0]
    print(f"Loading enrolled students from file: {target_file}")
    
    import pandas as pd
    df = pd.read_excel(target_file)

    # --- ここで元の順番を保持する列を追加 ---
    # reset_index()により、その時点の行番号が 'index' 列として追加されます
    # name='original_order' で列名を指定します
    df = df.reset_index().rename(columns={'index': 'original_order'})

    # 必要な列だけを抽出（追加した original_order を含める）
    df = df[['original_order', '学籍番号', '氏名']]
    df['学籍番号'] = df['学籍番号'].astype(str).str.upper().str.strip()
    # print(df.head())
    return df

def get_point(report_type, report_name, student_name):
    problems = load_problems_from_json(report_type, report_name)
    grades = load_grades_from_json(report_type, report_name, student_name)
   
    student_point = 0
    total_point = 0
    for problem_id in problems['order']:
        point = problems.get('points', {}).get(problem_id, 0)
        total_point += point
        grade = grades.get(f"grade_{problem_id}", 0)
        if grade == "circle":
            student_point += point
        elif grade == "triangle":
            student_point += point / 2
        # else: 0点として加算しない
        
    return student_point, total_point


def load_report_settings(app=None):
    if app is None:
        app = current_app
    """ファイルを読み込んでapp.configに格納する"""
    default_settings = {
        'THRESHOLD_S': 90,
        'THRESHOLD_A': 80,
        'THRESHOLD_B': 70,
        'THRESHOLD_C': 60,
        'RATIO_DETAIL_ONLY': 0.5,
        'RATIO_ANSWER_ONLY': 0.5,
        'RATIO_LATE': 0.8
    }
    
    if os.path.exists(os.path.join(app.config['SAVE_DIR'], app.config['REPORT_SETTINGS_FILE'])):
        try:
            with open(os.path.join(app.config['SAVE_DIR'], app.config['REPORT_SETTINGS_FILE']), 'r', encoding='utf-8') as f:
                saved_settings = json.load(f)
                # デフォルト値をベースに保存された値で上書き
                default_settings.update(saved_settings)
        except Exception as e:
            print(f"設定ファイルの読み込み失敗: {e}")
            
    # Flaskのconfigに反映
    for key, value in default_settings.items():
        app.config[key] = value
    return default_settings

def save_report_settings_to_file(data, app=None):
    if app is None:
        app = current_app
    """データをJSONファイルに保存し、app.configも更新する"""
    settings = {
        'THRESHOLD_S': int(data.get('s', 90)),
        'THRESHOLD_A': int(data.get('a', 80)),
        'THRESHOLD_B': int(data.get('b', 70)),
        'THRESHOLD_C': int(data.get('c', 60)),
        'RATIO_DETAIL_ONLY': float(data.get('ratio_detail_only', 0.5)),
        'RATIO_ANSWER_ONLY': float(data.get('ratio_answer_only', 0.5)),
        'RATIO_LATE': float(data.get('ratio_late', 0.8))
    }
    
    # 1. ファイルに保存
    with open(os.path.join(app.config['SAVE_DIR'], app.config['REPORT_SETTINGS_FILE']), 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)
        
    # 2. 現在のアプリ設定を更新
    for key, value in settings.items():
        app.config[key] = value

        

def summarize_problems(report_type, report_name, student_names):
    summary = {"total": {}, "correct": {}}

    for student_name in student_names:
        grades = load_grades_from_json(report_type, report_name, student_name)
        for k, v in grades.items():
            problem_id = k.replace("grade_", "")
            if problem_id not in summary["total"]:
                summary["total"][problem_id] = 0
                summary["correct"][problem_id] = 0
            if v in ["circle", "triangle", "cross"]:
                summary["total"][problem_id] += 1
                if v == "circle":
                    summary["correct"][problem_id] += 1
    return summary