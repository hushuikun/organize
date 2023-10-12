import os
import sys
import time
import shutil
import exiftool
import argparse
from tqdm import tqdm
from datetime import datetime, timedelta
from multiprocessing import Pool, freeze_support


TARGET_FOLDER = '.\MyLife'


def count_files_in_directory(path):
    # 遍历当前目录中的文件
    total_files = 0
    file_list = []
    for root, dirs, files in os.walk(path):
        if root.startswith(TARGET_FOLDER):
            continue
        total_files += len(files)
        for file in files:
            file_list.append(os.path.join(root, file))

    return total_files, file_list


def get_file_creation_date(file_path):
    try:
        with exiftool.ExifToolHelper(encoding='utf-8') as et:
            metadata = et.get_metadata(file_path.encode('gbk').decode('gbk'))
            if 'QuickTime:CreateDate' in metadata[0]:
                date = metadata[0]['QuickTime:CreateDate']
                date = datetime.strptime(date, '%Y:%m:%d %H:%M:%S') + timedelta(hours=8)
                return date.strftime('%Y-%m-%d %H:%M:%S')
            elif 'EXIF:DateTimeOriginal' in metadata[0]:
                return metadata[0]['EXIF:DateTimeOriginal']
            else:
                return None
    except exiftool.exceptions.ExifToolExecuteError:
        return None
    

def try_make_folder(folder_name):
    # 获取当前工作目录
    current_directory = os.getcwd()

    # 构造文件夹的完整路径
    folder_path = os.path.join(current_directory, folder_name)

    # 检查文件夹是否存在
    if not os.path.exists(folder_path):
        # 如果文件夹不存在，创建它
        os.makedirs(folder_path, exist_ok=True)


def task(file):
    if not (file.endswith('.py') or file.endswith('.exe')
            or file.endswith('.ini')):
        creation_date = get_file_creation_date(file)
        if creation_date is not None:
            target_path = f"{TARGET_FOLDER}\\" + "\\".join(
                creation_date.split(' ')[0].replace(
                    ':', '\\').replace('-', '\\').split('\\')[0: 2]
            ) 
        else:
            target_path = f"{TARGET_FOLDER}\\NoDate"
        try_make_folder(target_path)
        try:
            shutil.copy(file, target_path)
        except shutil.SameFileError:
            pass


if __name__ == '__main__':
    freeze_support()
    parser = argparse.ArgumentParser()
    parser.add_argument("--procs", type=int, default=10, choices=range(1, 33),
                        help="进程数, 默认为10, 范围为1-32")
    args, _ = parser.parse_known_args()
    # 指定要计算文件数的目录路径
    directory_path = "."
    total_files, file_list = count_files_in_directory(directory_path)
    with Pool(processes=args.procs) as pool:
        r = list(tqdm(pool.imap(task, file_list), total=total_files))
    print("The organization is done! Press Ctrl-C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sys.exit(0)
