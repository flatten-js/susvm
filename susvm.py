import os
import re
import time
import glob
import shutil
import zipfile
import argparse
import subprocess

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import chromedriver_binary



# Variables
PROJECT_NAME = 'susvm.py'
PROJECT_PATH = r'C:\Users\Flat\Desktop\susvm'

APP_PATH = r'C:\Users\Flat\Desktop\SUSPlayer2'
APP_MASTER_PATH = rf'{APP_PATH}\master'
APP_VERSIONS_PATH = rf'{APP_PATH}\versions'
_APP_TMP_PATH = rf'{APP_PATH}\tmp'

TYPE_INIT = 'init'
TYPE_BUILD = 'build'
TYPE_INSTALL = 'install'
TYPE_VERSIONS = 'versions'
TYPES = [TYPE_INIT, TYPE_BUILD, TYPE_INSTALL, TYPE_VERSIONS]

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

def versions():
    vers = glob.glob(rf'{APP_VERSIONS_PATH}\ver.*')
    for ver in sorted(vers): print(version(ver, 1))



# Types
if args.type == TYPE_INIT: init()
elif args.type == TYPE_BUILD: build()
elif args.type == TYPE_INSTALL: install(args.list, args.ver, args.pwd)
elif args.type == TYPE_VERSIONS: versions()
