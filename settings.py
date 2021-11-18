"""
Settings for MoM Production
    -- production.cfg
    -- define folder structure
        -- folders for data processing
        -- folders for data products

"""
import os
import configparser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

config = configparser.SafeConfigParser(allow_no_value=True)
config.read('%s/production.cfg' % (BASE_DIR))

# config directory
# base directory for downloading and processing data
WORKING_DIR = os.path.expanduser(config.get('general', 'WORKING_DIR'))
# base directory for the data products  
OUTPUT_DIR = os.path.expanduser(config.get('general', 'OUTPUT_DIR')) 

# watershed shp file
WATERSHED_DIR = os.path.join(BASE_DIR, 'watershed_shp')
WATERSHED_SHP = os.path.join(WATERSHED_DIR, "Watershed_pfaf_id.shp")
