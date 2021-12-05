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

def HWRF_download(hwrfurl):
    """ download rainfall data"""
    reqs = requests.get(hwrfurl)
    soup = BeautifulSoup(reqs.text,"html.parser")

    ascii_list = []
    for link in soup.find_all('a'):
        fstr = link.string
        if "rainfall.ascii" in fstr:
            fstr_local = os.path.join(settings.HWRF_PROC_DIR, fstr)
            if not os.path.exists(fstr_local):
                wgetcmd = "wget " + os.path.join(hwrfurl,fstr) + " -P " + settings.HWRF_PROC_DIR
                subprocess.call(wgetcmd, shell=True)
            ascii_list.append(fstr)
    
    return ascii_list

def HWRF_cron():
    """ main cron script"""
    
    # get date list
    datelist = generate_procesing_list()
    #print(datelist)

    if len(datelist) == 0:
        logging.info("no new data to process!")
        sys.exit(0)
    
    # switch to processing folder
    os.chdir(settings.HWRF_PROC_DIR)

    # download - process ascii
    for key in datelist:
        logging.info("check: " + key)
        a_list = HWRF_download(datelist[key])
        print(a_list)
        if len(a_list) == 0:
            logging.info("no rainfall data " + key)
            continue
        logging.info("processing " + key)
        #newtiff = process_rain(key,a_list)
        #newtiff = "hwrf."+ key +"rainfall.tiff"
        #logging.info("processing " + newtiff)
        #[hwrfcsv,dataflag] = HWRF_extract_by_watershed(newtiff)
        # if not dataflag:
        #     logging.info("no data: " + hwrfcsv)
        #     continue
        #logging.info("generated: " + hwrfcsv)
        #os.chdir(scriptdir)
        
        # run MoM update
        #testdate = key
        #update_HWRF_MoM(testdate,GFMS,GLoFAS,HWRFsummary,HWRFmom)


    os.chdir(settings.BASE_DIR)

    return

def main():
    HWRF_cron()

if __name__ == "__main__":
    main()