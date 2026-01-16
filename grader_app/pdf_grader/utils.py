import re
import os
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
from flask import current_app
from pathlib import Path
from PIL import Image


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

def get_submission(report_name, author_name, kind_name, rotate=0):
    base_dir = current_app.config['PDF_BASE_DIR']
    raw_dir = current_app.config['RAW_PDF_LIST']
    filtered_raw_dir = [s for s in raw_dir if report_name in s and kind_name in s]
    if len(filtered_raw_dir) > 1:
        print(f"警告: {author_name} の {kind_name} に該当するディレクトリが複数見つかりました。最初のものを使用します。")
    if len(filtered_raw_dir) == 0:
        print(f"警告: {author_name} の {kind_name} に該当するディレクトリが見つかりませんでした。")
    
    submissions = os.listdir(os.path.join(base_dir, filtered_raw_dir[0]))
    filtered_submissions = [s for s in submissions if author_name in s]
    if len(filtered_submissions) > 1:
        print(f"警告: {author_name} の提出物が複数見つかりました。最初のものを使用します。")
    if len(filtered_submissions) == 0:
        print(f"警告: {author_name} の提出物が見つかりませんでした。")
    
    report = filtered_raw_dir[0]
    author = filtered_submissions[0]
    images = get_images(report, author, rotate=rotate)
    return images