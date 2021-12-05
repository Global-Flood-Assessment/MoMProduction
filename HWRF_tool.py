"""
    HWRF_tool.py
        -- cron job script for HWRF data
"""

import sys, os, csv, json
import requests
from bs4 import BeautifulSoup
import logging
import subprocess
from osgeo import gdal
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask
import numpy as np
from rasterio import Affine
import math
from shapely.geometry import Point
import shutil
import zipfile
import settings

def check_status(adate):
    """ check if a give date is processed"""

    processed_list = os.listdir(settings.HWRF_SUM_DIR)
    processed = any(adate in x for x in processed_list)
    
    return processed

def generate_procesing_list():
    """ generate the processing list"""

    hosturl = settings.config.get('hwrf','HOST')
    reqs = requests.get(hosturl)
    soup = BeautifulSoup(reqs.text,"html.parser")
    
    datelist = {}
    for link in soup.find_all('a'):
        fstr = link.string
        if (fstr[:5] == 'hwrf.'):
            a_entry = fstr.split('.')[1]
            a_entry = a_entry.replace("/","")
            if check_status(a_entry):
                continue
            datelist[a_entry] = hosturl + fstr
    
    return datelist

def HWRF_cron():
    """ main cron script"""
    
    # get date list
    datelist = generate_procesing_list()
    print(datelist)

def main():
    HWRF_cron()

if __name__ == "__main__":
    main()