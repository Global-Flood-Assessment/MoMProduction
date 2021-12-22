"""
    VIIRS_tool.py
        -- process VIIRS data
        -- https://www.ssec.wisc.edu/flood-map-demo/ftp-link

        output:
        -- VIIRS_Flood_yyyymmdd.csv at VIIRS_summary
        -- VIIRS_1day_compositeyyyymmdd_flood.tiff at VIIRS_image
        -- VIIRS_5day_compositeyyyymmdd_flood.tiff at VIIRS_image
"""

import sys, os, csv, json
import argparse
import requests
import logging
import datetime
from osgeo import gdal
import rasterio
from rasterio.mask import mask
import numpy as np
import pandas as pd
import geopandas as gpd

import settings
from utilities import watersheds_gdb_reader, read_data
from VIIRS_MoM import update_VIIRS_MoM

def generate_adate():
    '''generate 1 day delay date'''

    previous_date = datetime.datetime.today() - datetime.timedelta(days=1)

    adate_str = previous_date.strftime("%Y%m%d")
    
    return adate_str

def check_status(adate):
    """ check if a give date is processed"""

    summaryfile = os.path.join(settings.VIIRS_SUM_DIR, "VIIRS_Flood_{}.csv".format(adate))
    if os.path.exists(summaryfile):
        processed = True
    else:
        processed = False

    return processed

def check_data_online(adate):
    """ check data is online for a given date"""
    # total 136 AOIs
    # 5-day composite
    # https://floodlight.ssec.wisc.edu/composite/RIVER-FLDglobal-composite_*_000900.part*.tif
    # 1-day composite
    # https://floodlight.ssec.wisc.edu/composite/RIVER-FLDglobal-composite1_*_000000.part*.tif
    
    baseurl = settings.config.get("viirs",'HOST')
    testurl_t = 'RIVER-FLDglobal-composite_{}_000000.part00{}.tif'
    for i in [1,2,3,4,5]:
        testurl = os.path.join(baseurl, testurl_t.format(adate,str(i)))
        r = requests.head(testurl)
        if r.status_code == 404:
            online = False
        else:
            online = True
            break

    return online

def build_tiff(adate):
    """download and build geotiff"""

    baseurl = settings.config.get("viirs",'HOST')
    day1url = os.path.join(baseurl,'RIVER-FLDglobal-composite1_{}_000000.part{}.tif')
    day5url = os.path.join(baseurl,'RIVER-FLDglobal-composite_{}_000000.part{}.tif')
    joblist = [{'product':'1day','url': day1url},{'product':'5day','url': day5url}]
    final_tiff = []
    for entry in joblist:
        tiff_file = "VIIRS_{}_composite{}_flood.tiff".format(entry['product'],adate)
        if os.path.exists(tiff_file):
            final_tiff.append(tiff_file)
            continue
        tiff_l = []
        for i in range(1,137):
            dataurl = entry['url'].format(adate,str(i).zfill(3))
            filename = dataurl.split('/')[-1]
            # try download file
            try:
                r = requests.get(dataurl, allow_redirects=True)
            except requests.RequestException as e:
                logging.warning("no download: " + dataurl)
                logging.waring('error:' + str(e))
                continue
            # may not have files for some aio
            if r.status_code == 404:
                continue
            open(filename,'wb').write(r.content)
            tiff_l.append(filename)
        vrt_file = tiff_file.replace('tiff','vrt')

        # build vrt
        vrt=gdal.BuildVRT(vrt_file, tiff_l)
        # translate to tiff
        # each tiff is 4GB in size
        gdal.Translate(tiff_file, vrt)     
        
        # generate compressed tiff
        small_tiff = os.path.join(settings.VIIRS_IMG_DIR, tiff_file)
        gdal.Translate(small_tiff,tiff_file, options="-of GTiff -co COMPRESS=LZW -co TILED=YES" )
        logging.info("generated: " + tiff_file)

        #remove all files
        vrt=None
        os.remove(vrt_file)

        if settings.config['storage'].getboolean('viirs_save'):
            print('zip downloaded file')
            zipped = os.path.join(settings.VIIRS_PROC_DIR,'VIIRS_{}.zip'.format(adate))
            zipcmd = f'zip {zipped} RIVER*.tif'
            os.system(zipcmd)
            logging.info("generated: " + zipped)

        for tif in tiff_l:
            os.remove(tif)

        final_tiff.append(tiff_file)
    
    return final_tiff  

def VIIRS_extract_by_mask(mask_json,tiff):
    with rasterio.open(tiff) as src:
        try:
            out_image, out_transform = mask(src, [mask_json['features'][0]['geometry']], crop=True)
        except ValueError as e:
            #'Input shapes do not overlap raster.'
            src = None
            area=0
            # return empty dataframe
            return area
    data = out_image[0]
    point_count = np.count_nonzero((data>140) & (data<201))
    src = None
    # total area
    #resolution is 375m
    area = point_count * 0.375 * 0.375
    return area

def VIIRS_extract_by_watershed(adate,tiffs):
    """extract data by wastershed"""

    watersheds = watersheds_gdb_reader()
    pfafid_list = watersheds.index.tolist()

    # two tiffs
    # VIIRS_1day_composite20210825_flood.tiff
    # VIIRS_5day_composite20210825_flood.tiff

    csv_dict = {}
    for tiff in tiffs:
        if "1day" in tiff:
            field_prefix = "oneday"
        if "5day" in tiff:
            field_prefix = "fiveday"
        csv_file = tiff.replace('.tiff','.csv')
        headers_list = ["pfaf_id",field_prefix+"Flood_Area_km",field_prefix+"perc_Area"]
        #write header
        with open(csv_file,'w') as f:   
            writer = csv.writer(f)
            writer.writerow(headers_list)
        with open(csv_file, 'a') as f:
            writer = csv.writer(f)
            for the_pfafid in pfafid_list:
                test_json = json.loads(gpd.GeoSeries([watersheds.loc[the_pfafid,'geometry']]).to_json())
                area = VIIRS_extract_by_mask(test_json,tiff)              
                perc_Area = area/watersheds.loc[the_pfafid]['area_km2']*100
                results_list = [the_pfafid,area,perc_Area]
                writer.writerow(results_list)
        csv_dict[field_prefix] = csv_file

    join = read_data(csv_dict['oneday'])
    join = join[join.onedayFlood_Area_km != 0]    

    join1 = read_data(csv_dict['fiveday'])
    join1 = join1[join1.fivedayFlood_Area_km != 0]

    merge = pd.merge(join.set_index('pfaf_id'), join1.set_index('pfaf_id'), on='pfaf_id', how='outer')
    merge.fillna(0, inplace=True) 

    #VIIRS_Flood_yyyymmdd.csv
    merged_csv = os.path.join(settings.VIIRS_SUM_DIR,"VIIRS_Flood_{}.csv".format(adate))
    merge.to_csv(merged_csv)  
    logging.info("generated: " + merged_csv)

    # need clean up
    os.remove(csv_dict['oneday'])
    os.remove(csv_dict['fiveday'])

    # remove tiff
    os.remove(tiffs[0])
    os.remove(tiffs[1])

    return

def VIIRS_cron(adate=""):
    """ main cron script"""

    # global basepath
    # basepath = os.path.dirname(os.path.abspath(__file__))
    # load_config()

    if adate=="":
        adate = generate_adate()

    if check_status(adate):
        logging.info("already processed: " + adate)
        return
        
    if not check_data_online(adate):
        logging.info("no data online: " + adate)
        return
    
    logging.info("Processing: " + adate)
    # change dir to VIIRSraw
    os.chdir(settings.VIIRS_PROC_DIR)

    # get two tiffs
    tiffs = build_tiff(adate)

    # extract data from tiffs
    VIIRS_extract_by_watershed(adate,tiffs)
    
    # update VIIRS MoM
    update_VIIRS_MoM(adate)
    
    os.chdir(settings.BASE_DIR)
    
    return

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-fd','--fixdate', dest='fixdate', type=str, help="rerun a cron job on a certian day")
    args = parser.parse_args()

    if(args.fixdate):
        VIIRS_cron(adate = args.fixdate)
    else: 
        VIIRS_cron()

if __name__ == "__main__":
    main()