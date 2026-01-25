#!/usr/bin/python3

#import yaml # package python3-pyyaml
import os
import sys
import string
import random
import shutil
import subprocess
import re

__version__ = "v0.1.30"
__abspath__ = os.path.abspath(__file__)


def doc_string():

    message =\
"""
Скрипт для синхронизации данных между env файлами, передаваемым Bimeister и тем, что расположен по пути /bimeister/releases/.env/
Аргументы:
    Обязательные:
    --env               - контур, где выполняется обновление(test, prod, demo)
    -r, --release       - номер устанавливаемой версии bimeister
    Опциональные:
    -dp, --default-pass - означает, что новый пароль для БД сгенерирован не будет. Вместо этого будет использован пароль из env-файла от Bimeister.

Пример запуска:
    $ ./sync_env_file.py --env test --release 143
    $ ./sync_env_file.py --env test --release 143 --default-pass
"""
    return message

def is_package_installed(package_name):
    try:
        output = subprocess.check_output(
            ['dnf', 'list', '--installed', package_name],
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        return True
    except subprocess.CalledProcessError:
        return False

def install_package(package_name, distro="rhel"):
    try:
        if distro == "debian":
            # For Debian/Ubuntu systems
            subprocess.run(['sudo', 'apt-get', 'install', '-y', package_name], check=True)
        elif distro == "rhel":
            # For RHEL/CentOS/Fedora systems
            subprocess.run(['sudo', 'dnf', 'install', '-y', package_name], check=True)
        elif distro == "arch_linux":
            # For Arch Linux
            subprocess.run(['sudo', 'pacman', '-S', '--noconfirm', package_name], check=True)
        print(f"Successfully installed {package_name}")
    except subprocess.CalledProcessError as err:
        print(f"Error installing {package_name}: {err}")

def create_file_backup(src: str, dst: str, follow_symlinks=True):
    """ Create a copy of the file. Function takes two arguments, which are full paths to the files. """

    try:
        shutil.copyfile(src, dst)
        return True
    except FileNotFoundError as err:
        print(f"Error: {err}")
        return False
    except PermissionError as err:
        print(f"Error: {err}")
        return False

def is_file_exists(file_path, err_msg=False) -> bool:
    """ Check if file exists. """

    if not os.path.isfile(file_path):
        if err_msg:
            print(f"Error: {file_path} file not found!")
        return False
    else:
        return True

def read_env_file(file) -> dict:
    """ Read provided .yaml file. """

    try:
        with open(file, mode='r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as err:
        print(f"YAML parsing error:\n{err}")
        return False
    except Exception as err:
        print(err)
        return False
    return data

def get_all_keys(data):
    """ Get all keys from env file, except bimeister_databases. """

    keys: list = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'bimeister_databases':
                continue
            keys.append(key)
            if isinstance(value, (dict, list)):
                keys.extend(get_all_keys(value))
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                keys.extend(get_all_keys(item))
    return keys

def are_var_types_equal(data_master, data_slave, env_file_slave_path) -> bool:
    """ Check if vars types of two provided arrays are equal. """

    if not len(data_master) == len(data_slave):
        print(f"{are_var_types_equal.__name__} Error: corrupted data between env files.")
        return False
    if not isinstance(data_master, dict) or not isinstance(data_slave, dict):
        print(f"{are_var_types_equal.__name__} Error: provided data must be dictionary.")
        return None
    for key in data_master.keys():
        if type(data_master[key]) != type(data_slave[key]):
            print(f"ValueError: incorrect type for '{key.upper()}' variable in {env_file_slave_path}.")
            return False
    return True

def check_revision(data_master: dict, data_slave: dict, env_file_master_path: str, env_file_slave_path: str) -> bool:
    """ Check if revision between two files is different. """

    # проверяем наличие переменных 'revision' и получаем их значения из обоих файлов
    if 'revision' in data_master.keys():
        revision_master = data_master['revision']
    else:
        print(f"Missing revision variable in {env_file_master_path} file.")
        sys.exit()
    if 'revision' in data_slave.keys():
        revision_slave = data_slave['revision']
    else:
        print(f"Missing revision variable in {env_file_slave_path} file.")
        sys.exit()

    # сравниваем номера ревизий
    if revision_slave > revision_master:
        print(f"Check revision values!\nError: Revision number of slave file {env_file_slave_path} is higher than master file {env_file_master_path}")
        sys.exit()
    elif revision_master == revision_slave:
        return False
    elif revision_master > revision_slave:
        return True
    else:
        print("Error: Unpredictible behaviour of the script logic during revision check!")
        sys.exit()

def check_if_new_databases_exist(data_master: dict, data_slave: dict, env_file_master_path: str, env_file_slave_path: str) -> list:
    """ Check if 'bimeister_databases' variable exists.
        Check if new databases appeared.
    """

    # проверяем наличие переменных 'bimeister_databases' и получаем их ключи
    if 'bimeister_databases' in data_master.keys():
        db_list_master: list = [db for db in data_master['bimeister_databases']]
    else:
        print(f"Missing 'bimeister_databases' variable in {env_file_master_path} file.")
        sys.exit()
    if 'bimeister_databases' in data_slave.keys():
        db_list_slave: list = [db for db in data_slave['bimeister_databases']]
    else:
        print(f"Missing 'bimeister_databases' variable in {env_file_slave_path} file.")
        sys.exit()

    new_db = list(set(db_list_master) - set(db_list_slave))
    db_in_slave_but_not_in_master = list(set(db_list_slave) - set(db_list_master))
    if db_in_slave_but_not_in_master:
        pass
        # print(f"Extra databases detected in {env_file_slave_path}:\n{db_in_slave_but_not_in_master}")
    return new_db

def write_data_into_yaml_file(data, file):
    """ Write provided data into yaml file. Provided data has to be a dictionary. """

    if not isinstance(data, dict):
        sys.exit("write_data_into_yaml_file: Provided data must be a dictionary!")
    with open(file, mode='w', encoding='utf-8') as f:
        yaml.dump(data, f, sort_keys=False)

def synchronize_databases_between_two_env_files(data_master, data_slave, path_to_env_slave, is_local_update=False):
    """ Validate differences between two env files in bimeister_databases block: master(from tools) and slave(/bimeister/releases/.env/)
        If there are any changes, synchronize them.
    """

    if not isinstance(data_master, dict) or not isinstance(data_slave, dict):
        sys.exit("synchronize_databases_between_two_env_files: Provided data must be a dictionary!")

    # получаем список БД из slave env и сравниваем со списком БД из master env
    slave_db_list: list = [db for db in data_slave['bimeister_databases']]
    keys_to_exclude: list = ['username', 'password']
    for key, value in data_master['bimeister_databases'].items():
        # если новая БД, то переносим все атрибуты
        if key not in slave_db_list:
            if is_local_update:
                data_slave['bimeister_databases'][key] = {k: v for k, v in value.items()}
            else:
                password = generate_password()
                data_slave['bimeister_databases'][key] = {k: password if k == 'password' else v for k, v in value.items()}
        # если БД уже существует, то актуализируем все атрибуты, за исключением 'username' и 'password'
        elif key in slave_db_list:
            data_slave['bimeister_databases'][key]: dict = {k: v for k, v in data_slave['bimeister_databases'][key].items() if k in value.keys()}
            updated_dict: dict = {k: v for k, v in value.items() if k not in keys_to_exclude}
            if not updated_dict:
                continue
            data_slave['bimeister_databases'][key].update(updated_dict)

    # удаляем БД из slave env, если такой БД нет в master env
    for db in slave_db_list:
        if not data_master['bimeister_databases'].get(db):
            del data_slave['bimeister_databases'][db]

    # поднимаем номер ревизии env slave до ревизии env master
    data_slave['revision'] = data_master['revision']

    write_data_into_yaml_file(data_slave, path_to_env_slave)

def generate_password(length=16):
    """ Function to generate random password. """

    password = []
    possible_characters: str = string.ascii_letters + string.digits
    for x in range(length):
        char = random.choice(possible_characters)
        password.append(char)
    password = ''.join(password)
    return password

def parse_args():
    """ Getting arguments from user's input. """

    try:
        args: str = ' '.join(sys.argv[1:])
        err_msg: str = "Missing required parameter:"

        # опция для использования короткого имени аргумента --release
        if '-r' in sys.argv[1:] and '--release' not in sys.argv[1:]:
            release_var: str = '-r'
        elif '-r' in sys.argv[1:] and '--release' in sys.argv[1:]:
            print(f"Error: arguments -r/--release are not allowed to use at the same time")
            sys.exit()
        else:
            release_var: str = "--release"

        # опция для использования короткого имени аргумента --default-pass
        if '-dp' in sys.argv[1:] and '--default-pass' not in sys.argv[1:]:
            default_pass_var: str = '-dp'
        elif '-dp' in sys.argv[1:] and '--default-pass' in sys.argv[1:]:
            print(f"Error: arguments -dp/--default-pass are not allowed to use at the same time")
            sys.exit()
        else:
            default_pass_var: str = "--default-pass"

        mandatory_args: list = [release_var, "--env"]
        optional_args: list = [default_pass_var]
        possible_args: list = mandatory_args + optional_args
        illegal_args: list = [arg for arg in sys.argv[1:] if arg not in possible_args and arg.startswith('--')]
        if illegal_args:
            print("Illegal arguments:", end=' ')
            print(*illegal_args, sep=', ')
            sys.exit()
        for arg in mandatory_args:
            if arg not in args.split():
                print(err_msg, arg)
                return False
        release_index: int = args.find(release_var)
        find_env: int = args.find("--env")
        find_no_pass_gen: int = args.find(default_pass_var)
        is_local_update: bool = False if find_no_pass_gen == -1 else True


        release_value: str = args[release_index:].split()[1]
        match = re.match(r"(\d+)", release_value)
        release_value = match.group(0) if match else 0
        env_file: str = args[find_env:].split()[1] + '.yaml'

        # path to master file from tools folder
        tools_dir_path: str = '/'.join(__abspath__.split('/')[:-2])
        env_file_master_path: str = f"{tools_dir_path}/env-files/{env_file}"
        # full path to slave file
        env_file_slave_path: str = f"/bimeister/releases/.env/{env_file}"

        return env_file_master_path, env_file_slave_path, int(release_value), is_local_update
    except Exception as err:
        print(err)
        return False

def main():
    """ Main logic of script execution. """

    if "--help" in ' '.join(sys.argv[1:]):
        print(doc_string())
        sys.exit()
    elif "--version" in ' '.join(sys.argv[1:]):
        print(__version__)
        sys.exit()
    check_args = parse_args()
    if check_args:
        env_file_master_path, env_file_slave_path, release_value, is_local_update = check_args[0], check_args[1], check_args[2], check_args[3]
    else:
        print(doc_string())
        sys.exit()
    if not is_file_exists(env_file_master_path, err_msg=True) or not is_file_exists(env_file_slave_path, err_msg=True):
        sys.exit()

    # читаем env файлы и записываем данные в словари
    data_master: dict = read_env_file(env_file_master_path)
    data_slave: dict = read_env_file(env_file_slave_path)
    if not data_master or not data_slave:
        sys.exit()

    new_db: list = check_if_new_databases_exist(data_master, data_slave, env_file_master_path, env_file_slave_path)

    # добываем все ключи(кроме 'bimeister_databases') из обоих env файлов
    keys_master: list = get_all_keys(data_master)
    keys_slave: list = get_all_keys(data_slave)
    missing_vars_in_slave = list(set(keys_master) - set(keys_slave))
    extra_vars_in_slave = list(set(keys_slave) - set(keys_master))
    if missing_vars_in_slave:
        print(f"Error: Missing variables in {env_file_slave_path}:\n{missing_vars_in_slave}")
        sys.exit()
    if extra_vars_in_slave:
        print(f"Error: Extra variables in {env_file_slave_path}:\n{extra_vars_in_slave}")
        sys.exit()

    # создаём бекап env файла в /bimeister/releases/.env/
    backup_filepath: str = env_file_slave_path + '.' + str(release_value - 1)
    if not is_file_exists(backup_filepath):
        is_file_created: bool = create_file_backup(env_file_slave_path, backup_filepath)
        if not is_file_created:
            sys.exit()

    # проверяем, что переменные env-файлов имеют одинаковые типы данных
    if not are_var_types_equal(data_master, data_slave, env_file_slave_path):
        sys.exit()

    is_revision_changed = check_revision(data_master, data_slave, env_file_master_path, env_file_slave_path)
    if not is_revision_changed and new_db:
        print(f"Error: revision numbers are equal, but new databases were detected in {env_file_master_path}\n{new_db}")
        sys.exit()
    if is_revision_changed:
        synchronize_databases_between_two_env_files(data_master, data_slave, env_file_slave_path, is_local_update=is_local_update)
        print("OK.")
    else:
        print("OK.")


if __name__ == '__main__':
    # check if package python3-pyyaml is installed
    package = "python3-pyyaml"
    if not is_package_installed(package):
        install_package(package)
    import yaml #requires package python3-pyyaml
    main()
