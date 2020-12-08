from php_formatter import PHPFormatter
import sys
import os
from os import listdir
from os.path import isfile, join, splitext
import logging


def _get_dirs_from_path(my_path):
    return [f for f in listdir(my_path) if not isfile(join(my_path, f))]


def _get_php_files_from_path(my_path):
    all_files = [f for f in listdir(my_path) if isfile(join(my_path, f))]
    js_files = []
    for f in all_files:
        f_name, f_ext = splitext(f)
        if f_ext == '.php':
            js_files.append(f)
    return js_files


def _get_result(file_path, file_name):
    formatter = PHPFormatter()
    formatter.process_php_file(file_path, file_name)
    PHPFormatter.formatted_files.append(formatter)
    PHPFormatter.all_changes.extend(formatter.get_invalid_tokens_list())
    PHPFormatter.old_file_names.append(formatter.file_name)
    PHPFormatter.new_file_names.append(formatter.new_file_name)


def _check_files_in_dir(my_path):
    php_files = _get_php_files_from_path(my_path)
    for php_file in php_files:
        _get_result(my_path, php_file)


def _check_rec(my_path):
    _check_files_in_dir(my_path)

    dirs = _get_dirs_from_path(my_path)
    for dir in dirs:
        _check_rec(join(my_path, dir))


def main():
    if len(sys.argv) == 2 and (sys.argv[1] == '-h' or sys.argv[1] == '--help'):
        print("Basic commands:")
        print("\t-h, --help\t\t\t\t: help menu")
        print("\t-v, --verify -(p|d|f) /..\t: verify your files(as output php_verification.log file);")
        print("\t\t\t\t\t\t  /.. - path to project, directory or file")

        print("\t-f, --format -(p|d|f) /..\t: format your files(as output php_fixing.log file);")
        print("\t\t\t\t\t\t  /.. - path to project, directory or file")
    elif len(sys.argv) == 4 and sys.argv[2] == '-p':
        _check_rec(sys.argv[3])
    elif len(sys.argv) == 4 and sys.argv[2] == '-d':
        _check_files_in_dir(sys.argv[3])
    elif len(sys.argv) == 4 and sys.argv[2] == '-f':
        _get_result('', sys.argv[3])
    else:
        print("Call help menu (-h, --help) for more details")
        exit()

    if sys.argv[1] == '-f' or sys.argv[1] == '--format':
        with open("php_fixing.log", "w") as f:
            pass
        logging.basicConfig(filename="php_fixing.log", level=logging.DEBUG)
        for file in PHPFormatter.formatted_files:
            file.setup_all_changes()
            file.save_to_file()
            file.save_fix_log()
    elif sys.argv[1] == '-v' or sys.argv[1] == '--verify':
        with open("php_verification.log", "w") as f:
            pass
        logging.basicConfig(filename="php_verification.log", level=logging.DEBUG)
        for file in PHPFormatter.formatted_files:
            file.setup_all_changes()
            file.save_ver_log()
