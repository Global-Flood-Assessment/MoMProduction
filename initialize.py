"""
Inititlize the setup
    -- create the folder structures defined in production.cfg
    -- check username/password in production.cfg
    -- unzip watershed.shp
"""

import os, sys
from zipfile import ZipFile

from settings import *

def create_dir(apath):
    '''create dir with a path'''
    if not os.path.exists(apath):
        print("crate " + apath)
        os.makedirs(apath, exist_ok=True)

print("task: check folder stucture")

create_dir(WORKING_DIR)
# task: create the sub folders inside working_dir
for key in config['processing']:
    subfolder = os.path.join(WORKING_DIR, config.get("processing",key))
    create_dir(subfolder)

# task: check ftp user/password
user = config.get("glofas", "user")
passwd = config.get('glofas', "passwd")

if ('?' in user or '?' in passwd):
    print('Action required: production.cfg')
    print('Please fill in user/passwd in glofas section')
    sys.exit()
else:
    print('Task: check user/passwd')

# task: check if shp file is unzipped
if not os.path.exists(WATERSHED_SHP):
    print("Task: unzip watershed.shp.zip")
    with ZipFile(WATERSHED_SHP + '.zip' ,'r') as zipObj:
        zipObj.extractall(WATERSHED_DIR)
else:
    print("Task: watershed shp is already unzipped")

print("System initilization is completed!")