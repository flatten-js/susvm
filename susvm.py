import os
import re
import sys
import time
import glob
import shutil
import zipfile
import textwrap
import threading
import subprocess
import pyautogui as gui
from operator import itemgetter
from pyhooked import Hook, KeyboardEvent

import argparse
from argparse import RawTextHelpFormatter

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException



# Variables
def _env(key, exit = True):
    try:
        return os.environ[key]
    except KeyError as e:
        print('Environment variable not found:', e)

        name = str(e).replace('$', '')
        print('From Powershell with administrator privileges, set up the following \n')
        print(f"    [System.Environment]::SetEnvironmentVariable({name}, 'Path you want to set', 'User')")

        if not exit: return None
        return sys.exit()

ENV_SUSVM = 'SUSVM'
ENV_SUSVM_APP = f'{ENV_SUSVM}_APP'
ENV_SUSVM_HELPER = f'{ENV_SUSVM}_HELPER'

PROJECT_NAME = 'susvm.py'
PROJECT_PATH = _env(ENV_SUSVM)

APP_NAME = 'SUSPlayer.exe'
APP_CONFIG_NAME = 'Config.ini'
APP_PATH = _env(ENV_SUSVM_APP)
APP_MASTER_PATH = rf'{APP_PATH}\master'
APP_VERSIONS_PATH = rf'{APP_PATH}\.versions'
APP_VERSION_PATH = rf'{APP_PATH}\.version'
_APP_TMP_PATH = rf'{APP_PATH}\.tmp'

CHROME_DRIVER = r'driver\chromedriver.exe'
REQUIREMENTS = 'requirements.txt'

TYPE_UPDATE = 'update'
TYPE_BUILD = 'build'
TYPE_INIT = 'init'
TYPE_INSTALL = 'install'
TYPE_VERSIONS = 'versions'
TYPE_USE = 'use'
TYPE_START = 'start'

LOOP_LIMIT = 10



# Methods
def version(str, depth = 0):
    return re.search(r'ver\.(\d+\.\d+)*', str).group(depth)

def resource_path(path):
    try:
        dir_path = sys._MEIPASS
    except:
        dir_path = os.path.dirname(__file__)

    return f'{dir_path}\\{path}'

def chrome_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--single-process')
    options.add_argument('--blink-settings=imagesEnabled=false')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver = webdriver.Chrome(resource_path(CHROME_DRIVER), options=options)

    driver.command_executor._commands['send_command'] = ('POST', '/session/$sessionId/chromium/send_command')
    driver.execute('send_command', params = {
        'cmd': 'Page.setDownloadBehavior',
        'params': { 'behavior': 'allow', 'downloadPath': _APP_TMP_PATH }
      }
    )

    return driver

def tmp_status():
    start = time.time()
    timeout = 60

    while True:
        diff = time.time() - start
        if timeout <= diff: break

        tmp = os.listdir(_APP_TMP_PATH)
        if tmp:
            exs = list(map(os.path.splitext, tmp))
            if all([not '.crdownload' == ex[1] for ex in exs]): return tmp

        time.sleep(1)

    return None

def unzip(from_, to, mkdir = False):
    with zipfile.ZipFile(from_) as zf:
        if mkdir: os.mkdir(to)
        zf.extractall(to)

def kill(pid):
    subprocess.call(['taskkill', '/F', '/T', '/PID', str(pid)], stdout = subprocess.DEVNULL)

def unstable_app_open(path = None, cmd = None, cwd = None, wait = 0):
    kwargs = { 'cwd': cwd, 'shell': cmd }
    process = subprocess.Popen(cmd or path, **kwargs)
    if cmd: process._kill = lambda: kill(process.pid)

    time.sleep(wait)
    return process

def type_keys(keys):
    keys = keys.split('+')
    for key in keys: gui.keyDown(key)
    for key in keys: gui.keyUp(key)

def args_parse(args):
    args = vars(args)
    del args['handler']
    return itemgetter(*args.keys())(args)

def config_load(path):
    dict = {}

    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            result = re.search(r'^(\w+)=([\w.]*)$', line)
            if not result: continue
            dict.update([result.groups()])

    return dict

def config_sync(master_path, native_path):
    master = config_load(master_path)

    with open(native_path, 'r', encoding='utf-8') as fr:
        lines = fr.read()
        for k, v in master.items(): lines = re.sub(rf'(?<={k}=).*', v, lines)
        with open(native_path, 'w', encoding='utf-8') as fw: fw.write(lines)

def cmd_options(name, *args):
    return ' '.join(map(lambda v: f'--{name} {v}', args))

def dedent(str):
    return textwrap.dedent(str)[1:-1]



# Core
def update(args):
    docs = """
        To update the VM itself, Git needs to be installed.
        See Also: https://sukkiri.jp/technologies/devtools/git/git_win.html

        * Run it from the root directory of susvm.

        This is not necessary if this is the second or later time or if you have cloned directly from Git.

            Create a new repository
                C:\> git init

            Create an association with a remote repository
                C:\> git remote add origin https://github.com/flatten-js/susvm

            Get the latest data from the remote branch
                C:\> git pull

            Forcibly overwrite the local master
                C:\> git reset --hard origin/master

            Explicitly set up an upstream branch
                C:\> git branch --set-upstream-to=origin/master master


        Get the latest data from the remote branch
            C:\> git pull
    """

    print(dedent(docs))

def build(args):
    binarys = [f'{PROJECT_PATH}\\{CHROME_DRIVER};./driver']
    datas = [f'{PROJECT_PATH}\\{REQUIREMENTS};.']

    add_binarys = cmd_options('add-binary', *binarys)
    add_datas = cmd_options('add-data', *datas)

    cmd = f'pyinstaller {PROJECT_PATH}\\{PROJECT_NAME} --onefile {add_binarys} {add_datas}'
    subprocess.call(cmd)

def init(args):
    developer = args_parse(args)

    if developer:
        subprocess.call(f'pip install -r {resource_path(REQUIREMENTS)}')
        print('')

        print('The environment in which it was run')
        subprocess.call('python -V && pip -V', shell=True)

    if not os.path.exists(APP_PATH):
        os.mkdir(APP_PATH)

    if not os.path.exists(APP_MASTER_PATH):
        os.mkdir(APP_MASTER_PATH)

    if not os.path.exists(APP_VERSIONS_PATH):
        os.mkdir(APP_VERSIONS_PATH)

    if not os.path.exists(APP_VERSION_PATH):
        os.mkdir(APP_VERSION_PATH)

def _install_list(driver):
    vers = []

    for i in range(LOOP_LIMIT):
        containers = driver.find_elements_by_xpath('//div[div[@role="alert"]]')

        for container in containers:
            a = container.find_element_by_xpath('.//a[@title]')
            title = a.get_attribute('title')
            vers.append(version(title, 1))

        next = driver.find_element_by_xpath('//a[contains(text(), "次へ")]')
        if driver.current_url == next.get_attribute('href'): break

        next.click()

    return vers

def _install_link(driver, ver):
    for i in range(LOOP_LIMIT):
        try:
            return driver.find_element_by_xpath(f'//a[contains(@title, "{ver}.")]')
        except NoSuchElementException:
            next = driver.find_element_by_xpath('//a[contains(text(), "次へ")]')
            if driver.current_url == next.get_attribute('href'): break

            next.click()

    return None

def _install_try(driver, pwd):
    form = driver.find_element_by_name('agree')
    input = form.find_element_by_name('password')
    input.send_keys(pwd)
    form.submit()

    try:
        success = driver.find_element_by_class_name('alert-success')
        return True
    except NoSuchElementException:
        danger = driver.find_element_by_class_name('alert-danger')
        message = danger.find_elements_by_tag_name('p')[1].text

        if message == 'ダウンロードパスワードの認証に失敗しました。':
            print('Incorrect password.')
        else:
            print('An unexpected error has occurred.')

    return False

def install(args):
    is_list, ver, pwd = args_parse(args)

    if ver in _versions(): return print(f'Version {ver} is already installed.')

    driver = chrome_driver()
    driver.get('https://ux.getuploader.com/kousi_taiko/search?q=SUSPlayer')

    if is_list:
        vers = _install_list(driver)
        print('Available versions')
        for ver in sorted(vers): print(f'  {ver}')
        return driver.quit()

    link = _install_link(driver, ver)
    if link is None:
        print('The specified version was not found.')
        print('See all available versions with `susvm install -l`.')
        return driver.quit()

    # Disable target=_blank and go to the installation page
    url = link.get_attribute('href')
    driver.get(url)

    success = _install_try(driver, pwd)
    if not success: return driver.quit()

    os.mkdir(_APP_TMP_PATH)

    try:
        form = driver.find_element_by_name('agree')
        form.submit()

        files = tmp_status()
        if not files: return print('Timeout.')

        zip = files[0]
        unzip(f'{_APP_TMP_PATH}\\{zip}', f'{APP_VERSIONS_PATH}\\{version(zip)}', mkdir=True)
    except Exception as e:
        return print(e)
    finally:
        shutil.rmtree(_APP_TMP_PATH)
        driver.quit()

    print('Installation has been completed successfully.')

def _versions():
    vers = glob.glob(rf'{APP_VERSIONS_PATH}\ver.*')
    return [version(ver, 1) for ver in sorted(vers)]

def versions(args):
    use_ver = glob.glob(rf'{APP_VERSION_PATH}\ver.*')
    if use_ver: use_ver = version(use_ver[0], 1)

    for ver in _versions():
        if use_ver == ver: print(f'* {ver} (Currently using executable)')
        else: print(f'  {ver}')

def use_sync(ver):
    for file in os.listdir(APP_MASTER_PATH):
        target_path = f'{ver}\\{file}'

        if file == APP_CONFIG_NAME:
            config_sync(f'{APP_MASTER_PATH}\\{file}', target_path)
            continue

        if os.path.islink(target_path): os.unlink(target_path)
        elif os.path.isdir(target_path): shutil.rmtree(target_path)
        elif os.path.isfile(target_path): os.remove(target_path)

        os.symlink(f'{APP_MASTER_PATH}\\{file}', target_path)

def use(args):
    ver = args_parse(args)

    vers = glob.glob(rf'{APP_VERSIONS_PATH}\ver.{ver}')
    if not vers:
        print('The specified version was not found.')
        print('See all available versions with `susvm versions`.')
        return

    use_ver = glob.glob(rf'{APP_VERSION_PATH}\ver.*')
    if use_ver: shutil.rmtree(use_ver[0])

    ver = vers[0]
    use_ver = version(ver)
    use_ver_path = f'{APP_VERSION_PATH}\{use_ver}'
    shutil.copytree(ver, use_ver_path)

    use_sync(use_ver_path)

    print(f'Now using SUSPlayer {use_ver}')

def _start_app_shortcat():
    TARGET_KEYS = ['I', 'K']

    pressing = []
    lock = False
    start = 0

    def handle_events(args):
        nonlocal lock, start
        key = args.current_key

        if not isinstance(args, KeyboardEvent): return
        if lock and key == 'Escape': return

        if args.event_type == 'key down':
            if not key in pressing: pressing.append(key)
        elif args.event_type == 'key up':
            pressing.remove(key)

        if set(TARGET_KEYS) == set(pressing):
            if not start: start = time.time()
            diff = time.time() - start

            if not lock and 1.5 <= diff:
                lock = True
                type_keys('esc')
        else:
            lock = False
            start = 0

    hk = Hook()
    hk.handler = handle_events
    hk.hook()

def _start_app_intercept(app):
    sub = threading.Thread(target = _start_app_shortcat)
    sub.setDaemon(True)
    sub.start()

    while True:
        time.sleep(0.01)
        if app.poll() == 0: break

def start(args):
    right, left, is_full = args_parse(args)

    vers = glob.glob(rf'{APP_VERSION_PATH}\ver.*')
    if not vers:
        print('The version you want to use is not selected.')
        print('Use `susvm use` to specify the version you want to use.')
        return

    ver = vers[0]

    app = unstable_app_open(cmd = APP_NAME, cwd = ver, wait = 2)
    if right or left: type_keys(f'win+shift+{right or left}')

    if is_full:
        path = _env(ENV_SUSVM_HELPER, False)
        if path:
            helper_app = unstable_app_open(path, wait = 2)
            helper_app.kill()
        else:
            print('')

    print(f'{version(ver)} is running now')

    try:
        _start_app_intercept(app)
    except KeyboardInterrupt:
        app._kill()



# Arguments
epilog = """
    Environment Variables

    Setup

        From Powershell with administrator privileges, set up the following
        [System.Environment]::SetEnvironmentVariable('ENV_NAME', 'Path you want to set', 'User')

        You will need to restart the shell after configuration.
        If it still does not update, reboot the OS.

    Required

        SUSVM: Path to the project folder (recommended: %USERPROFILE%\.susvm)
        SUSVM_APP: Path of the application folder to manage (recommended: %USERPROFILE%\Desktop\SUSPlayer)
        PATH: Path of the distribution folder in the project folder (recommended: %SUSVM%\dist)

    Optional

        SUSVM_HELPER:
            Path to the executable file to make it virtual full screen.
            See Also: [
                https://github.com/Codeusa/Borderless-Gaming,
                https://store.steampowered.com/app/388080/Borderless_Gaming
            ]
"""

parser = argparse.ArgumentParser(epilog = dedent(epilog), formatter_class = RawTextHelpFormatter)
subparsers = parser.add_subparsers()

parser_update = subparsers.add_parser(TYPE_UPDATE, help='Documentation for updating the VM itself')
parser_update.set_defaults(handler=update)

parser_build = subparsers.add_parser(TYPE_BUILD, help='Build to executables for developers')
parser_build.set_defaults(handler=build)

parser_init = subparsers.add_parser(TYPE_INIT, help='Initialize the application directory creation, etc')
parser_init.add_argument('-d', '--developer', action='store_true', help='Set up as a developer')
parser_init.set_defaults(handler=init)

parser_install = subparsers.add_parser(TYPE_INSTALL, help='Install the app by specifying the version')
parser_install.add_argument('-l', '--list', action='store_true', help='List the installable versions')
parser_install.add_argument('-v', '--ver', help='Specify the version to install')
parser_install.add_argument('-p', '--pass', default='', help='Specify the password for installation')
parser_install.set_defaults(handler=install)

parser_versions = subparsers.add_parser(TYPE_VERSIONS, help='List the installed versions')
parser_versions.set_defaults(handler=versions)

parser_use = subparsers.add_parser(TYPE_USE, help='Specify the version to be used from the installed version')
parser_use.add_argument('ver', help='Specify the version to use')
parser_use.set_defaults(handler=use)

parser_start = subparsers.add_parser(TYPE_START, help='Start the app based on the version used')
parser_start.add_argument('-r', '--right', action='store_const', const='right', help='Move the application to the right between monitors')
parser_start.add_argument('-l', '--left', action='store_const', const='left', help='Move the application to the left between monitors')
parser_start.add_argument('-f', '--full', action='store_true', help='Make the application window virtual full screen')
parser_start.set_defaults(handler=start)

args = parser.parse_args()

if hasattr(args, 'handler'): args.handler(args)
else: parser.print_help()
