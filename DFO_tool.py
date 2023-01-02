"""
DFO_tool.py

Download and process DFO data

Two main function:
    * DFO_cron : run the daily cron job
    * DFO_cron_fix: rerun cron-job for a given date
"""


import csv
import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import date, datetime

import geopandas
import numpy as np
import pandas as pd
import rasterio
import requests
from bs4 import BeautifulSoup
from rasterio.mask import mask

from DFO_MoM import update_DFO_MoM
from settings import *
from utilities import from_today, watersheds_gdb_reader

# for command line mode, no need for cron-job
# from progressbar import progress

# total number of hdf files
DFO_TOTAL_TILES = 223
DFO_MINIMUM_TILES = 221


def get_real_date(year, day_num):
    """get the real date"""

    # allData/61/MCDWD_L3_NRT/2021/021

    # year,day_num = foldername.split("/")[-2:]
    res = datetime.strptime(str(year) + "-" + str(day_num), "%Y-%j").strftime("%Y%m%d")

    return res


def check_status(adate):
    """check if a give date is processed"""

    processed_list = os.listdir(DFO_SUM_DIR)
    processed = any(adate in x for x in processed_list)

    return processed


def get_hosturl():
    """get the host url"""
    baseurl = config.get("dfo", "HOST")
    cur_year = date.today().year
    hosturl = os.path.join(baseurl, str(cur_year))

    return hosturl


def generate_procesing_list():
    """generate list of date to process"""
    hosturl = get_hosturl()
    reqs = requests.get(hosturl)
    soup = BeautifulSoup(reqs.text, "html.parser")
    cur_year = hosturl[-4:]
    datelist = {}
    # get the today in str
    today_str = date.today().strftime("%Y%m%d")
    for link in soup.find_all("a"):
        day_num = link.string
        if not day_num.isdigit():
            continue
        real_date = get_real_date(cur_year, day_num)
        # compare date in iso str
        # skip the later date, there is no data
        if real_date > today_str:
            continue
        # check if the date is already processed
        if check_status(real_date):
            continue
        datelist[day_num] = real_date

    return datelist


def dfo_download(subfolder):
    """download a subfolder"""

    # check if there is unfinished download
    d_dir = os.path.join(DFO_PROC_DIR, subfolder)
    if os.path.exists(d_dir):
        # is file cases
        if os.path.isfile(d_dir):
            os.remove(d_dir)
        else:
            # remove the subfolder
            shutil.rmtree(d_dir)

    dfokey = config.get("dfo", "TOKEN")
    dataurl = os.path.join(get_hosturl(), subfolder)
    wgetcmd = 'wget -r --no-parent -R .html,.tmp -nH -l1 --cut-dirs=8 {dataurl} --header "Authorization: Bearer {key}" -P {downloadfolder}'
    wgetcmd = wgetcmd.format(dataurl=dataurl, key=dfokey, downloadfolder=DFO_PROC_DIR)
    # print(wgetcmd)
    exitcode = subprocess.call(wgetcmd, shell=True)
    if not exitcode == 0:
        # something wrong with downloading
        logging.warning("download failed: " + dataurl)
        sys.exit()

    return


def dfo_extract_by_mask(vrt_file, mask_json):
    """extract data for a single watershed"""

    with rasterio.open(vrt_file) as src:
        try:
            out_image, out_transform = mask(
                src, [mask_json["features"][0]["geometry"]], crop=True
            )
        except ValueError as e:
            #'Input shapes do not overlap raster.'
            # print(e)
            src = None
            # return empty dataframe
            return 0

    # extract data
    no_data = src.nodata
    # extract the values of the masked array
    # print(out_image)
    data = out_image[0]
    point_count = np.count_nonzero(data == 3)
    src = None

    # total area
    d = point_count * 0.25 * 0.25

    return d


def dfo_extract_by_watershed(vtk_file):
    """extract data by all the watersheds"""

    watersheds = watersheds_gdb_reader()
    pfaf_id_list = watersheds.index.tolist()

    headerprefix = os.path.basename(vtk_file).split("_")[1]
    if "_CS_" in vtk_file:
        headerprefix = "1-Day_CS"

    headers_list = [
        "pfaf_id",
        headerprefix + "_TotalArea_km2",
        headerprefix + "_perc_Area",
    ]
    summary_file = os.path.basename(vtk_file)[:-4] + ".csv"
    if not os.path.exists(summary_file):
        with open(summary_file, "w") as f:
            writer = csv.writer(f)
            writer.writerow(headers_list)
    else:
        # already processed,
        return

    # count = 0
    with open(summary_file, "a") as f:
        writer = csv.writer(f)

        for pfaf_id in pfaf_id_list:
            # print(the_aqid, count, " out of ", len(aqid_list))
            # count += 1
            # progress(count,  len(pfaf_id_list), status='pfaf_id')
            # extract mask
            test_json = json.loads(
                geopandas.GeoSeries([watersheds.loc[pfaf_id, "geometry"]]).to_json()
            )
            # plot check
            dfoarea = dfo_extract_by_mask(vtk_file, test_json)

            DFO_TotalArea = dfoarea
            DFO_Area_percent = DFO_TotalArea / watersheds.loc[pfaf_id]["area_km2"] * 100

            results_list = [
                pfaf_id,
                "{:.3f}".format(DFO_TotalArea),
                "{:.3f}".format(DFO_Area_percent),
            ]
            writer.writerow(results_list)

    return


def DFO_process(folder, adate):
    """processing dfo folder

    folder structure
    allData/61/MCDWD_L3_NRT/2021/021
        |-Flood 1-Day 250m
        |-Flood 1-Day CS 250m
        |-Flood 2-Day 250m
        |-Flood 3-Day 250m
        Flood_3-Day_250m.vrt
        Flood_2-Day_250m.vrt
        Flood_1-Day_CS_250m.vrt
        Flood_1-Day_250m.vrt
    """

    hdffolder = os.path.join(DFO_PROC_DIR, folder)
    if os.path.isfile(hdffolder):
        logging.warning("Not downloaded properly: " + folder)
        return

    # switch to working directory
    os.chdir(hdffolder)

    floodlayer = [
        "Flood 1-Day 250m",
        "Flood 1-Day CS 250m",
        "Flood 2-Day 250m",
        "Flood 3-Day 250m",
    ]
    # create sub folder if necessary
    for flood in floodlayer:
        subfolder = flood.replace(" ", "_")
        if not os.path.exists(subfolder):
            os.mkdir(subfolder)

    # MCDWD_L3_NRT.A2021022.h06v04.061.hdf
    # HDF4_EOS:EOS_GRID:"MCDWD_L3_NRT.A2021022.h06v04.061.hdf":Grid_Water_Composite:"Flood 1-Day 250m"
    # HDF4_EOS:EOS_GRID:"MCDWD_L3_NRT.A2021022.h06v04.061.hdf":Grid_Water_Composite:"Flood 1-Day CS 250m"
    # HDF4_EOS:EOS_GRID:"MCDWD_L3_NRT.A2021022.h06v04.061.hdf":Grid_Water_Composite:"Flood 2-Day 250m"
    # HDF4_EOS:EOS_GRID:"MCDWD_L3_NRT.A2021022.h06v04.061.hdf":Grid_Water_Composite:"Flood 3-Day 250m"
    # HDF4_EOS:EOS_GRID:"{HDF}":Grid_Water_Composite:"{floodLAYER}"

    # scan hdf files
    hdffiles = []
    for entry in os.listdir():
        if entry[-4:] != ".hdf":
            continue
        HDF = entry
        hdffiles.append(HDF)

    # check the number of files
    # need check the date first
    ddays = from_today(adate)
    # for the previous day, just process what ever it has
    if ddays >= 0:
        if len(hdffiles) < DFO_TOTAL_TILES:
            logging.warning("Not enough files: " + folder)
            return

    # one step one image operation
    vrt_list = []
    for flood in floodlayer:
        subfolder = flood.replace(" ", "_")
        # geotiff convert
        for HDF in hdffiles:
            nameprefix = "_".join(HDF.split(".")[1:3])
            inputlayer = f'HDF4_EOS:EOS_GRID:"{HDF}":Grid_Water_Composite:"{flood}"'
            tiff = nameprefix + "_" + subfolder
            outputtiff = os.path.join(subfolder, tiff + ".tiff")
            if not os.path.exists(outputtiff):
                # gdal cmd
                gdalcmd = (
                    f"gdal_translate -of GTiff -co Tiled=Yes {inputlayer} {outputtiff}"
                )
                # convert geotiff
                os.system(gdalcmd)
        # build vrt
        gdalcmd = f"gdalbuildvrt {subfolder}.vrt {subfolder}/*.tiff"
        # print(gdalcmd)
        os.system(gdalcmd)

        vrt = f"{subfolder}.vrt"
        vrt_list.append(vrt)
        # extract flood data
        dfo_extract_by_watershed(vrt)

        # build geotiff
        if "3-Day" in vrt:
            # tiff =  outputfolder + os.path.sep + "DFO_image/DFO_" + datestr + "_" + vrt.replace(".vrt",".tiff")
            # DFO_20210603_Flood_3-Day_250m.tiff
            tiff = "DFO_{datestr}_{layer}.tiff".format(datestr=adate, layer=subfolder)
            tiff = os.path.join(DFO_IMG_DIR, tiff)
            # gdal_translate -co TILED=YES -co COMPRESS=PACKBITS -of GTiff Flood_1-Day_250m.vrt Flood_1-Day_250m.tiff
            # gdaladdo -r average Flood_1-Day_250m.tiff 2 4 8 16 32
            gdalcmd = (
                f"gdal_translate -co TILED=YES -co COMPRESS=LZW -of GTiff {vrt} {tiff}"
            )
            os.system(gdalcmd)
            # build overview
            # gdalcmd = f'gdaladdo -r average {tiff} 2 4 8 16 32'
            # os.system(gdalcmd)

        # delete tiff folder
        if os.path.exists(subfolder):
            shutil.rmtree(subfolder)

    # merge flood data into one file
    csv_list = []
    for vrt in vrt_list:
        csvfile = vrt.replace(".vrt", ".csv")
        pdc = pd.read_csv(csvfile)
        csv_list.append(pdc)

    merged = csv_list[0].merge(csv_list[1], on="pfaf_id")
    merged = merged.merge(csv_list[2], on="pfaf_id")
    merged = merged.merge(csv_list[3], on="pfaf_id")

    # save output
    summary_csv = os.path.join(DFO_SUM_DIR, "DFO_{}.csv".format(adate))
    merged.to_csv(summary_csv)
    logging.info("generated: " + summary_csv)

    # zip the original folder
    if config["storage"].getboolean("dfo_save"):
        zipped = os.path.join(DFO_PROC_DIR, "DFO_{}.zip".format(adate))
        zipcmd = f"zip -r -0 {zipped} ./*"
        os.system(zipcmd)
        logging.info("generated: " + zipped)

    # remove all hdf file in the folder
    for entry in os.listdir():
        if ".hdf" in entry:
            os.remove(entry)

    # switch back script folder
    os.chdir(BASE_DIR)

    return


def DFO_cron():
    """cron job to process DFO"""

    datelist = generate_procesing_list()
    print(datelist)
    sys.exit()

    if len(datelist) == 0:
        logging.info("no new data to process!")
        sys.exit(0)

    for key in datelist:
        logging.info("download: " + key)
        dfo_download(key)
        logging.info("download finished!")
        logging.info("processing: " + key)
        # process data
        # key: folder name
        # datelist[key]: real date
        DFO_process(key, datelist[key])
        # run DFO_MoM
        update_DFO_MoM(datelist[key])
        logging.info("processing finished: " + key)

    return


def main():
    DFO_cron()


if __name__ == "__main__":
    main()
