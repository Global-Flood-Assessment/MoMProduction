"""
Inititlize the setup
    -- create the folder structures defined in production.cfg
    -- check username/password, token in production.cfg
    -- unzip watershed.shp
"""

import os
import shutil
import sys
from zipfile import ZipFile

# firt check production.cfg
if not os.path.exists("production.cfg"):
    shutil.copyfile("sample_production.cfg", "production.cfg")
    print("please check the production.cfg, run initilize again.")
    sys.exit()

from settings import *


def create_dir(apath):
    """create dir with a path"""
    if not os.path.exists(apath):
        print("crete " + apath)
        os.makedirs(apath, exist_ok=True)


print("task: check folder stucture")

# create working dir
create_dir(WORKING_DIR)
# task: create the sub folders inside working_dir
for key in config["processing_dir"]:
    subfolder = os.path.join(WORKING_DIR, config.get("processing_dir", key))
    create_dir(subfolder)

# create product dir
create_dir(PRODUCT_DIR)
# task: create the sub folders inside product_dir
product_sub_folders = ["summary", "image", "MoM"]
product_with_subfolder = ["GFMS", "HWRF", "DFO", "VIIRS"]
for key in config["products_dir"]:
    subfolder = os.path.join(PRODUCT_DIR, config.get("products_dir", key))
    create_dir(subfolder)
    if key.upper() in product_with_subfolder:
        for product_sub in product_sub_folders:
            create_dir(os.path.join(subfolder, key.upper() + "_" + product_sub))

# task: check ftp user/password, key
user = config.get("glofas", "USER")
passwd = config.get("glofas", "PASSWD")

if "?" in user or "?" in passwd:
    print("Action required: production.cfg")
    print("Please fill in USER/PASSED in glofas section")
    sys.exit()

dfo_token = config.get("dfo", "TOKEN")
if "?" in dfo_token:
    print("Action required: production.cfg")
    print("Please fill in TOKEN in dfo section")
    sys.exit()

# task: check if shp file is unzipped
if not os.path.exists(WATERSHED_SHP):
    print("Task: unzip watershed.shp.zip")
    with ZipFile(WATERSHED_SHP + ".zip", "r") as zipObj:
        zipObj.extractall(WATERSHED_DIR)
else:
    print("Task: watershed shp is already unzipped")

print("System initilization is completed!")
