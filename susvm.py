import os
import argparse
import subprocess



# Variables
PROJECT_NAME = 'susvm.py'
PROJECT_PATH = r'C:\Users\Flat\Desktop\susvm'

APP_PATH = r'C:\Users\Flat\Desktop\SUSPlayer2'
APP_MASTER_PATH = rf'{APP_PATH}\master'
APP_VERSIONS_PATH = rf'{APP_PATH}\versions'
_APP_TMP_PATH = rf'{APP_PATH}\tmp'

TYPE_INIT = 'init'
TYPE_BUILD = 'build'
TYPES = [TYPE_INIT, TYPE_BUILD]



# Arguments
parser = argparse.ArgumentParser()

parser.add_argument('type', choices = TYPES)

args = parser.parse_args()



# Methods



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



# Types
if args.type == TYPE_INIT: init()
elif args.type == TYPE_BUILD: build()
