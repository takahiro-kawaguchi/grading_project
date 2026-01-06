import os
import zipfile

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