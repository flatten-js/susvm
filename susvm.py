import os
import re
import time
import glob
import shutil
import zipfile
import argparse
import threading
import subprocess
import pyautogui as gui
from pyhooked import Hook, KeyboardEvent

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import chromedriver_binary



# Variables
PROJECT_NAME = 'susvm.py'
PROJECT_PATH = r'C:\Users\Flat\Desktop\susvm'

APP_NAME = 'SUSPlayer.exe'
APP_PATH = r'C:\Users\Flat\Desktop\SUSPlayer2'
APP_MASTER_PATH = rf'{APP_PATH}\master'
APP_VERSIONS_PATH = rf'{APP_PATH}\versions'
_APP_TMP_PATH = rf'{APP_PATH}\tmp'

HELPER_APP_PATH = r'C:\Program Files (x86)\Steam\steamapps\common\Borderless Gaming\BorderlessGaming.exe'

TYPE_INIT = 'init'
TYPE_BUILD = 'build'
TYPE_INSTALL = 'install'
TYPE_VERSIONS = 'versions'
TYPE_SYNC = 'sync'
TYPE_START = 'start'
TYPES = [TYPE_INIT, TYPE_BUILD, TYPE_INSTALL, TYPE_VERSIONS, TYPE_SYNC, TYPE_START]

LOOP_LIMIT = 10



# Arguments
parser = argparse.ArgumentParser()

parser.add_argument('type', choices = TYPES)
parser.add_argument('-l', '--list', action = 'store_true', help='Display the list')
parser.add_argument('-v', '--ver', help='Specify the version')
parser.add_argument('-p', '--pwd', default='', help='Specify the password')

args = parser.parse_args()



# Methods
def version(str, depth = 0):
    return re.search(r'ver\.(\d+\.\d+)*', str).group(depth)

def chrome_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--blink-settings=imagesEnabled=false')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver = webdriver.Chrome(options=options)

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



# Core
def init():
    if not os.path.exists(APP_PATH):
        os.mkdir(APP_PATH)

    if not os.path.exists(APP_MASTER_PATH):
        os.mkdir(APP_MASTER_PATH)

    if not os.path.exists(APP_VERSIONS_PATH):
        os.mkdir(APP_VERSIONS_PATH)

def build():
    subprocess.call(f'pyinstaller {PROJECT_PATH}\\{PROJECT_NAME} --onefile')

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

def install(is_list, ver, pwd):
    if ver in _versions(): return print(f'Version {ver} is already installed.')

    driver = chrome_driver()
    driver.get('https://ux.getuploader.com/kousi_taiko/search?q=SUSPlayer')

    if is_list:
        vers = _install_list(driver)
        for ver in sorted(vers): print(ver)
        return driver.quit()

    link = _install_link(driver, ver)
    if link is None:
        print('The specified version was not found.')
        print('See all available versions with `susvm install -l`.')
        return driver.quit()

    # Disable target=_blank and go to the installation page
    driver.get(link.get_attribute('href'))

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

def versions():
    for ver in _versions(): print(ver)

def sync():
    vers = glob.glob(rf'{APP_VERSIONS_PATH}\ver.*')

    for ver in vers:
        for file in os.listdir(APP_MASTER_PATH):
            target_path = f'{ver}\\{file}'

            if os.path.islink(target_path): os.unlink(target_path)
            elif os.path.isdir(target_path): shutil.rmtree(target_path)
            elif os.path.isfile(target_path): os.remove(target_path)

            os.symlink(f'{APP_MASTER_PATH}\\{file}', target_path)

    print('Synchronization has been completed successfully.')

def _start_app_shortcat():
    TARGET_KEYS = ['I', 'K']

    pressing = []
    lock = False
    start = 0

    def handle_events(args):
        global lock, start
        key = args.current_key

        if not isinstance(args, KeyboardEvent): return

        if args.event_type == 'key down':
            if not key in pressing: pressing.append(key)
        elif args.event_type == 'key up':
            pressing.remove(key)

        if set(TARGET_KEYS) == set(pressing):
            if not start: start = time.time()
            diff = time.time() - start

            if not lock and 2 <= diff:
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

def start(ver):
    ver = ver or '*'
    vers = glob.glob(rf'{APP_VERSIONS_PATH}\ver.{ver}')

    if not vers:
        print('The specified version was not found.')
        print('See all available versions with `susvm versions`.')
        return

    # ToDo: Perform exact version comparison
    ver = max(vers)

    app = unstable_app_open(cmd = APP_NAME, cwd = ver, wait = 2)
    type_keys('win+shift+right')

    helper_app = unstable_app_open(HELPER_APP_PATH, wait = 2)
    helper_app.kill()

    try:
        _start_app_intercept(app)
    except KeyboardInterrupt:
        app._kill()



# Types
if args.type == TYPE_INIT: init()
elif args.type == TYPE_BUILD: build()
elif args.type == TYPE_INSTALL: install(args.list, args.ver, args.pwd)
elif args.type == TYPE_VERSIONS: versions()
elif args.type == TYPE_SYNC: sync()
elif args.type == TYPE_START: start(args.ver)
