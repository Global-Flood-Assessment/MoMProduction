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

def process_rain(adate,TC_Rain):
    """process rainfall data"""

    ## VRT template to read the csv
    vrt_template="""<OGRVRTDataSource>
        <OGRVRTLayer name='{}'>
            <SrcDataSource>{}</SrcDataSource>
            <GeometryType>wkbPoint</GeometryType>
            <GeometryField encoding="PointFromColumns" x="lon" y="lat" z="Z"/>
        </OGRVRTLayer>
    </OGRVRTDataSource>"""

    ## Read each text file and create the separate tiff file
    for i in TC_Rain:
        with open(i,'r') as f:
            variable=csv.reader(f, delimiter=' ') 
            row_count=1 
            for row in variable:
                if row_count == 1: 
                    while ('' in row):
                        row.remove('')
                    XLC=float(row[0]) 
                    XRC=float(row[1]) 
                    YBC=float(row[2]) 
                    YTC=float(row[3])
                    res=float(row[4])
                    nrows=float(row[5])
                    ncol=float(row[6])
                    row_count = row_count + 1
        df = (pd.read_table(i, skiprows=1, delim_whitespace=True, names=('lat', 'lon', 'Z'))).fillna(-999)
        df.sort_values(by=["lat","lon"], ascending=[False, True])
        df=df[['lon','lat','Z']]
        df = df[df.lon >= XLC]
        df = df[df.lon <= XRC]
        df = df[df.lat >= YBC]
        df = df[df.lat <= YTC]
        df = df[df.Z > 0]
        df.to_csv(i.replace(".ascii",".csv"),index=False, sep=" ")
        with open(i.replace(".ascii",".vrt"),"w") as g:
            g.write(vrt_template.format(i.replace(".ascii",""),i.replace(".ascii",".csv")))
        g.close()
        r=gdal.Rasterize(i.replace(".ascii",".tiff"),i.replace(".ascii",".vrt"),outputSRS="EPSG:4326",xRes=res, yRes=res,attribute="Z", noData=-999)
        r=None
        os.remove(i.replace(".ascii",".csv"))

    ##merge all  tiffs file als
    # nd delete the individual tiff, vrt and ascii file 

    TC_Rain_tiff=[]
    for i in TC_Rain:
        TC_Rain_tiff.append(i.replace(".ascii",".tiff"))

    filename="hwrf."+ adate +"rainfall.vrt"
    raintiff = filename.replace(".vrt",".tiff")
    vrt = gdal.BuildVRT(filename, TC_Rain_tiff)
    gdal.Translate(raintiff, vrt)
    vrt=None
    
    # no need
    #gdalcmd = "gdal_translate -of GTiff " + filename + " " + raintiff
    #subprocess.call(gdalcmd, shell=True)

    # create a zipfile
    zip_file="hwrf."+ adate +"rainfall.zip"
    with zipfile.ZipFile(zip_file, 'w',zipfile.ZIP_DEFLATED) as zipObj:
        for i in TC_Rain_tiff:
            asfile = i.replace(".tiff",".ascii")
            zipObj.write(asfile)
    
    for i in TC_Rain_tiff:
        os.remove(i)
        os.remove(i.replace(".tiff",".ascii"))
        os.remove(i.replace(".tiff",".vrt"))

    return raintiff

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
        if len(a_list) == 0:
            logging.info("no rainfall data " + key)
            continue
        logging.info("processing " + key)
        newtiff = process_rain(key,a_list)
        print(newtiff)
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