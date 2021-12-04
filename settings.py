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
BASE_DATA_DIR = os.path.join(BASE_DIR,'data')

config = configparser.ConfigParser(allow_no_value=True)
config.read(os.path.join(BASE_DIR,"production.cfg"))

# config directory
# base directory for downloading and processing data
WORKING_DIR = os.path.expanduser(config.get('general', 'WORKING_DIR'))
# base directory for the data products  
PRODUCT_DIR = os.path.expanduser(config.get('general', 'PRODUCT_DIR')) 

# config GLOFAS directory
GLOFAS_PROC_DIR = os.path.join(WORKING_DIR,config.get('processing_dir', 'glofas'))
GLOFAS_DIR = os.path.join(PRODUCT_DIR,config.get('products_dir', 'GLOFAS'))

# config GFMS directory
GFMS_PROC_DIR = os.path.join(WORKING_DIR,config.get('processing_dir', 'gfms'))
GFMS_DIR = os.path.join(PRODUCT_DIR,config.get('products_dir', 'GFMS'))
GFMS_SUM_DIR = os.path.join(GFMS_DIR,"GFMS_summary")
GFMS_IMG_DIR = os.path.join(GFMS_DIR,"GFMS_image")
GFMS_MOM_DIR = os.path.join(GFMS_DIR,"GFMS_MoM")

# config DFO directory
DFO_PROC_DIR = os.path.join(WORKING_DIR,config.get('processing_dir', 'dfo'))
DFO_DIR = os.path.join(PRODUCT_DIR,config.get('products_dir', 'DFO'))
DFO_SUM_DIR = os.path.join(DFO_DIR,"DFO_summary")
DFO_IMG_DIR = os.path.join(DFO_DIR,"DFO_image")
DFO_MOM_DIR = os.path.join(DFO_DIR,"DFO_MoM")

# config VIIRS directory
VIIRS_PROC_DIR = os.path.join(WORKING_DIR,config.get('processing_dir', 'VIIRS'))
VIIRS_DIR = os.path.join(PRODUCT_DIR,config.get('products_dir', 'VIIRS'))
VIIRS_SUM_DIR = os.path.join(VIIRS_DIR,"VIIRS_summary")
VIIRS_IMG_DIR = os.path.join(VIIRS_DIR,"VIIRS_image")
VIIRS_MOM_DIR = os.path.join(VIIRS_DIR,"VIIRS_MoM")

# config HWRF directory
HWRF_PROC_DIR = os.path.join(WORKING_DIR,config.get('processing_dir', 'hwrf'))
HWRF_DIR = os.path.join(PRODUCT_DIR,config.get('products_dir', 'HWRF'))
HWRF_SUM_DIR = os.path.join(HWRF_DIR,"HWRF_summary")
HWRF_IMG_DIR = os.path.join(HWRF_DIR,"HWRF_image")
HWRF_MOM_DIR = os.path.join(HWRF_DIR,"HWRF_MoM")

# config watershed shp file
WATERSHED_DIR = os.path.join(BASE_DIR, 'watershed_shp')
WATERSHED_SHP = os.path.join(WATERSHED_DIR, "Watershed_pfaf_id.shp")

# setup logging
# generate a new log for each month
todays_date = date.today()
logfile = "{year}_{month}.log".format(year=todays_date.year,month=todays_date.month)
logfile = os.path.join(WORKING_DIR,config.get('processing_dir', 'logs'),logfile)
logging.basicConfig(filename=logfile, format='%(asctime)s - %(module)s - %(levelname)s : %(message)s', level=logging.INFO)
