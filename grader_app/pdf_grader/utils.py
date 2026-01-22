import re
import os
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
from flask import current_app
from pathlib import Path
from PIL import Image
import pandas as pd
import json
from datetime import datetime


def extract_keys(filename):
    match = re.search(r'第(\d+)回', filename)
    return int(match.group(1)) if match else float('inf')

def get_report_list(dirlist):
    """ディレクトリリストからレポート番号を抽出し、ソートされたリストを返す"""
    dirlist = set([d.split("の提出")[0] for d in dirlist])
    return sorted(dirlist, key=extract_keys)

def get_total_pdf_pages(pdf_path_list):
    """PDFファイルのリストを受け取り、合計ページ数を返す"""
    total_pages = 0
    for pdf_path in pdf_path_list:
        try:
            with open(pdf_path, 'rb') as f:
                reader = PdfReader(f)
                total_pages += len(reader.pages)
        except Exception as e:
            print(f"警告: {pdf_path} のページ数を読み込めませんでした。エラー: {e}")
            # エラーが発生したPDFは0ページとして扱うか、例外を投げるかを選択
            pass
    return total_pages


def convert_pdf_to_images(pdf_path_list, savedir, img_name):
    """
    PDFを画像に変換する。
    期待されるページ数と既存の画像数が一致しない場合は、再生成する。
    """
    # 保存先ディレクトリのフルパス

    image_root = current_app.config['IMAGE_DIR']
    image_subpath = current_app.config['IMAGE_SUBPATH']

    def get_url_path(filename):
        # ブラウザ用に "pdf_images/student_id/page0.png" のような形を作る
        # OSの区切り文字 (\) を URLの区切り文字 (/) に置換
        return Path(image_subpath).joinpath(savedir, filename).as_posix()
    
    save_full_dir = os.path.join(image_root, savedir)
    os.makedirs(save_full_dir, exist_ok=True)

    # 1. 期待される総ページ数を計算
    total_expected_pages = get_total_pdf_pages(pdf_path_list)
    if total_expected_pages == 0:
        print("処理するべきPDFページがありません。")
        return []

    # 2. 既存の画像ファイル数をカウント
    pattern = re.compile(rf"^{re.escape(img_name)}_page(\d+)\.png$")
    existing_images = [f for f in os.listdir(save_full_dir) if pattern.match(f)]
    num_existing_images = len(existing_images)

    # 3. ページ数と画像数を比較
    if total_expected_pages == num_existing_images:
        print(f"画像は既に生成済みです ({num_existing_images}枚)。キャッシュを利用します。")
        # ファイル名順にソートしてパスのリストを返す
        existing_images.sort(key=lambda x: int(pattern.match(x).group(1)))
        return [get_url_path(f) for f in existing_images]

    # 4. 不一致の場合、既存の画像を削除して再生成
    print(f"ページ数/画像数に不一致を検出しました (期待: {total_expected_pages}, 既存: {num_existing_images})。画像を再生成します。")
    for img_file in existing_images:
        os.remove(os.path.join(save_full_dir, img_file))

    # --- 以下、画像の生成処理 ---
    try:
        all_image_paths = []
        page_counter = 0
        for pdf_path in pdf_path_list:
            images = convert_from_path(pdf_path)
            for img in images:
                img_path = os.path.join(save_full_dir, f"{img_name}_page{page_counter}.png")
                img.save(img_path, "PNG")
                all_image_paths.append(get_url_path(f"{img_name}_page{page_counter}.png"))
                page_counter += 1
        
        return all_image_paths

    except Exception as e:
        print(f"エラー: PDFから画像の変換中に問題が発生しました。エラー: {e}")
        # エラー発生時は、専用のエラー画像パスを返す
        return [get_url_path("error.png")]
    

def get_students(report_index):
    dirlist = current_app.config['PDF_LIST']
    raw_dirlist = current_app.config['RAW_PDF_LIST']
    students = []
    report = dirlist[report_index]
    for r in raw_dirlist:
        if report in r:
            students.extend(os.listdir(os.path.join(current_app.config['PDF_BASE_DIR'], r)))
    students = [s.split("_")[0] for s in students]
    students = sorted(list(set(students)))
    return students

def get_images(report, author, rotate):
    img_name = author
    pdf_path_list = [
        os.path.join(
            current_app.config['PDF_BASE_DIR'],
            report,
            author,
            pdf
        ) for pdf in os.listdir(os.path.join(current_app.config['PDF_BASE_DIR'], report, author))
    ]
    images = convert_pdf_to_images(pdf_path_list, report + "/" + author, img_name)
    if rotate != 0:
        images = rotate_images(images, rotate)
    return images

def get_pdfs(report_index, author_index):
    sorted_dirlist = current_app.config['PDF_LIST']
    author_list = get_students(report_index)
    author = author_list[author_index]
    pdfs = os.listdir(os.path.join(current_app.config['PDF_BASE_DIR'], sorted_dirlist[report_index], author))
    return pdfs

def rotate_images(images, rotate):
    images_new = []
    for img_path in images:
        rotated_img_path = img_path.replace(".png", f"_rotated{rotate}.png")
        if not os.path.exists(rotated_img_path):
            img = Image.open(img_path)
            img = img.rotate(rotate*90, expand=True)
            img.save(rotated_img_path)
        images_new.append(rotated_img_path)
    return images_new

def get_submission(report_name, student_name, kind_name, rotate=0):
    base_dir = current_app.config['PDF_BASE_DIR']
    raw_dir = current_app.config['RAW_PDF_LIST']
    filtered_raw_dir = [s for s in raw_dir if report_name in s and kind_name in s]
    if len(filtered_raw_dir) > 1:
        raise Exception(f"警告: {student_name} の {kind_name} に該当するディレクトリが複数見つかりました。")
    if len(filtered_raw_dir) == 0:
        print(f"警告: {student_name} の {kind_name} に該当するディレクトリが見つかりませんでした。")
        return []
    
    submissions = os.listdir(os.path.join(base_dir, filtered_raw_dir[0]))
    filtered_submissions = [s for s in submissions if student_name in s]
    if len(filtered_submissions) > 1:
        raise Exception(f"警告: {student_name} の提出物が複数見つかりました。")
    if len(filtered_submissions) == 0:
        print(f"警告: {student_name} の提出物が見つかりませんでした。")
        return []
    
    report = filtered_raw_dir[0]
    author = filtered_submissions[0]
    images = get_images(report, author, rotate=rotate)
    return images

def issubmitted(report_name, student_name, kind_name):
    base_dir = current_app.config['PDF_BASE_DIR']
    raw_dir = current_app.config['RAW_PDF_LIST']
    filtered_raw_dir = [s for s in raw_dir if report_name in s and kind_name in s]
    if len(filtered_raw_dir) != 1:
        return False
    submissions = os.listdir(os.path.join(base_dir, filtered_raw_dir[0]))
    filtered_submissions = [s for s in submissions if student_name in s]
    return len(filtered_submissions) == 1


def get_scores(report_index):
    from flask import jsonify
    from grader_app.utils import get_point
    report_name = current_app.config['PDF_LIST'][report_index]
    student_list = get_students(report_index)
    scores = {}
    for student_name in student_list:
        point, total_point = get_point('pdf', report_name, student_name)
        if total_point != 0:
            point = round(point/total_point * 100, 2)
        scores[student_name] = point
    return scores


def get_report_data_context(mode='status'):
    """
    提出状況またはスコアのデータを生成する共通ヘルパー関数
    mode: 'status' (◎, 詳, 答, ×) または 'scores' (数値)
    """
    from grader_app.utils import get_enrolled_students
    ratio_detail_only = current_app.config.get('RATIO_DETAIL_ONLY', 0.5)
    ratio_answer_only = current_app.config.get('RATIO_ANSWER_ONLY', 0.5)
    ratio_late = current_app.config.get('RATIO_LATE', 0.8)
    
    df_students = get_enrolled_students('pdf')
    if df_students is None:
        return None

    report_list = current_app.config['PDF_LIST']
    all_unlisted_data = []

    submission_files = [f for f in os.listdir(current_app.config['PDF_BASE_DIR']) if f.endswith(".json")]

    for i, report_name in enumerate(report_list):
        scores_data = get_scores(i)
        # get_scoresの戻り値が辞書(scores["data"])か、直接辞書かで調整してください
        scores = scores_data.get("data", scores_data) if isinstance(scores_data, dict) else scores_data
        
        students_names = get_students(i)
        current_report_rows = []
        
        submission_file_detail = [f for f in submission_files if report_name.split("-")[1] in f and '詳細' in f]
        submission_file_answer = [f for f in submission_files if report_name.split("-")[1] in f and '解答のみ' in f]

        if len(submission_file_detail) == 0:
            submission_date_detail = {}
        else:
            submission_date_detail = json.load(open(os.path.join(current_app.config['PDF_BASE_DIR'], submission_file_detail[0]), 'r', encoding='utf-8') )
        if len(submission_file_answer) == 0:
            submission_date_answer = {}
        else:
            submission_date_answer = json.load(open(os.path.join(current_app.config['PDF_BASE_DIR'], submission_file_answer[0]), 'r', encoding='utf-8') )
        
        # print(submission_date_detail)
        deadline_detail = submission_date_detail.get("deadline", "")
        deadline_answer = submission_date_answer.get("deadline", "")

        for student_name in students_names:
            parts = student_name.split()
            number = parts[0].upper().strip()
            name = " ".join(parts[1:]).strip() if len(parts) > 1 else ""
            
            sub_detail = issubmitted(report_name, student_name, '詳細')
            sub_answer = issubmitted(report_name, student_name, '解答のみ')
            
            is_late = False
            if sub_detail:
                date_detail = submission_date_detail["submissions"][number]
                is_late = check_delay(deadline_detail, date_detail)
            if sub_answer:
                date_answer = submission_date_answer["submissions"][number]
                is_late = is_late or check_delay(deadline_answer, date_answer)



            if mode == 'status':
                suffix = "（遅）" if is_late else ""
                if sub_detail and sub_answer: val = "◎"+suffix
                elif sub_detail: val = "詳"+suffix
                elif sub_answer: val = "答"+suffix
                else: val = "×"
            else: # scores mode
                base_score = scores.get(student_name, 0)
                if sub_detail and sub_answer: val = base_score
                elif sub_detail: val = base_score * ratio_detail_only
                elif sub_answer: val = base_score * ratio_answer_only
                else: val = 0

                if is_late:
                    val = val * ratio_late
            
            current_report_rows.append({'学籍番号': number, '氏名': name, report_name: val})

        status_df = pd.DataFrame(current_report_rows)
        
        # 名簿内へのマージ
        df_students = pd.merge(df_students, status_df.drop(columns=['氏名']), on='学籍番号', how='left')
        fill_val = "×" if mode == 'status' else 0
        df_students[report_name] = df_students[report_name].fillna(fill_val)

        # 名簿外の抽出
        unlisted = status_df[~status_df['学籍番号'].isin(df_students['学籍番号'])]
        all_unlisted_data.append(unlisted)

    # 名簿外学生の集約
    df_unlisted = None
    if all_unlisted_data:
        for temp_df in all_unlisted_data:
            if df_unlisted is None:
                df_unlisted = temp_df
            else:
                df_unlisted = pd.merge(df_unlisted, temp_df, on=['学籍番号', '氏名'], how='outer')
        if df_unlisted is not None:
            df_unlisted = df_unlisted.fillna("×" if mode == 'status' else 0)

    stats = {}

    if mode == 'scores' and not df_students.empty:
        # report_list に含まれる列（各課題の点数）だけで平均を計算
        df_students['平均点'] = df_students[report_list].mean(axis=1).round(1)
        
        # 評価ロジック
        def calculate_grade(score):
            if score >= current_app.config.get('THRESHOLD_S', 90): return 'S' # 90以上をS、それ以外をA~Dに振り分け
            if score >= current_app.config.get('THRESHOLD_A', 80): return 'A'
            if score >= current_app.config.get('THRESHOLD_B', 70): return 'B'
            if score >= current_app.config.get('THRESHOLD_C', 60): return 'C'
            return 'D'
        
        df_students['評価'] = df_students['平均点'].apply(calculate_grade)
        
        counts = df_students['評価'].value_counts()
        total = len(df_students)
        
        # S, A, B, C, D の順番で辞書を作成
        for grade in ['S', 'A', 'B', 'C', 'D']:
            count = int(counts.get(grade, 0))
            ratio = round((count / total) * 100, 1) if total > 0 else 0
            stats[grade] = {'count': count, 'ratio': ratio}

    # 名簿外学生の集約
    # ... (既存の集約処理) ...
    if mode == 'scores' and df_unlisted is not None and not df_unlisted.empty:
        df_unlisted['平均点'] = df_unlisted[report_list].mean(axis=1).round(1)
        df_unlisted['評価'] = df_unlisted['平均点'].apply(calculate_grade)

    # original_orderでソート
    df_students = df_students.sort_values('original_order')

    return {
        "enrolled": df_students.to_dict(orient='records'),
        "unlisted": df_unlisted.to_dict(orient='records') if df_unlisted is not None else [],
        "columns": df_students.columns.tolist(),
        "report_list": report_list,
        "mode": mode,
        "stats": stats
    }



    df_students = df_students.sort_values('original_order')

    return {
        "enrolled": df_students.to_dict(orient='records'),
        "unlisted": df_unlisted.to_dict(orient='records') if df_unlisted is not None else [],
        "columns": df_students.columns.tolist(),
        "report_list": report_list,
        "mode": mode
    }


def parse_japanese_date(date_str):
    """
    「2025年 10月 9日(木曜日) 17:23」のような形式をdatetimeに変換する
    """
    # 正規表現で数字部分だけを抽出する (年, 月, 日, 時, 分)
    match = re.search(r'(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日.*?\s*(\d{1,2}):(\d{1,2})', date_str)
    
    if match:
        year, month, day, hour, minute = map(int, match.groups())
        return datetime(year, month, day, hour, minute)
    return None

def check_delay(deadline_str, submission_str):
    """
    遅延判定メインロジック
    """
    deadline = parse_japanese_date(deadline_str)
    submission = parse_japanese_date(submission_str)

    if not deadline or not submission:
        return "日付形式が正しくありません"

    if submission > deadline:
        # delay = submission - deadline
        # 1時間以上の遅延、1分以上の遅延など詳細を出すことも可能
        return True
    else:
        return False