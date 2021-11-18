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

# watershed shp file
WATERSHED_SHP = os.path.join(BASE_DIR, 'watershed_shp')