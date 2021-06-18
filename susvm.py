import argparse
import subprocess



# Variables
PROJECT_NAME = 'susvm.py'
PROJECT_PATH = r'C:\Users\Flat\Desktop\susvm'

TYPE_BUILD = 'build'



# Arguments
parser = argparse.ArgumentParser()

parser.add_argument('type', choices = [TYPE_BUILD])

args = parser.parse_args()



# Methods



# Core
def build():
    subprocess.call(f'pyinstaller {PROJECT_PATH}\\{PROJECT_NAME} --onefile')



# Types
if args.type == TYPE_BUILD: build()
