"""
Settings for MoM Production
    -- production.cfg
    -- define folder structure
        -- folders for data processing
        -- folders for data products

"""
import os
import configparser
from datetime import date
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

config = configparser.ConfigParser(allow_no_value=True)
config.read(os.path.join(BASE_DIR,"production.cfg"))

# config directory
# base directory for downloading and processing data
WORKING_DIR = os.path.expanduser(config.get('general', 'WORKING_DIR'))
# base directory for the data products  
PRODUCT_DIR = os.path.expanduser(config.get('general', 'PRODUCT_DIR')) 

# config processing directory
glofas_dir = os.path.join(WORKING_DIR,config.get('processing', 'glofas_dir'))

# config products directory
GLOFAS_DIR = os.path.join(PRODUCT_DIR,config.get('products', 'GLOFAS_DIR'))
# watershed shp file
WATERSHED_DIR = os.path.join(BASE_DIR, 'watershed_shp')
WATERSHED_SHP = os.path.join(WATERSHED_DIR, "Watershed_pfaf_id.shp")

# setup logging
# generate a new log for each month
todays_date = date.today()
logfile = "{year}_{month}.log".format(year=todays_date.year,month=todays_date.month)
logfile = os.path.join(WORKING_DIR,config.get('processing', 'logs'),logfile)
logging.basicConfig(filename=logfile, format='%(asctime)s - %(module)s - %(levelname)s : %(message)s', level=logging.INFO)
