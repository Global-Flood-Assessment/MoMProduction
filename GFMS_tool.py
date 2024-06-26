"""
GFMS_tool.py

Download and process GFMS and GloFAS data

Two main function:
    * GFMS_cron : run the daily cron job
    * GFMS_cron_fix: rerun cron-job for a given date
"""

import csv
import glob
import json
import logging
import math
import os
import sys
from datetime import date, datetime, timedelta

import geopandas
import numpy as np
import pandas as pd
import rasterio
import requests
from rasterio import Affine  # or from affine import Affine
from rasterio.mask import mask
from shapely.geometry import Point

from GFMS_MoM import flood_severity

# from HWRF_MoM import update_HWRF_MoM, update_HWRFMoM_DFO_VIIRS, final_alert_pdc
from HWRF_MoM import hwrf_workflow
from settings import *
from utilities import findLatest, hwrf_today, watersheds_gdb_reader

# no need for cron-job
# from progressbar import progress


def GloFAS_download():
    """download glofas data from ftp"""
    ftpsite = {}
    ftpsite["host"] = config.get("glofas", "HOST")
    ftpsite["user"] = config.get("glofas", "USER")
    ftpsite["passwd"] = config.get("glofas", "PASSWD")
    ftpsite["directory"] = config.get("glofas", "DIRECTORY")
    from ftplib import FTP

    ftp = FTP(host=ftpsite["host"], user=ftpsite["user"], passwd=ftpsite["passwd"])
    ftp.cwd(ftpsite["directory"])
    file_list = ftp.nlst()
    job_list = []
    for txt in file_list:
        save_txt = os.path.join(GLOFAS_PROC_DIR, txt)
        if os.path.exists(save_txt):
            continue
        with open(save_txt, "wb") as fp:
            ftp.retrbinary("RETR " + txt, fp.write)
            if "threspoints_" in txt:
                job_list.append((txt.split(".")[0]).replace("threspoints_", ""))
    ftp.quit()

    return job_list


def GloFAS_process():
    """process glofas data"""

    new_files = GloFAS_download()

    if len(new_files) == 0:
        logging.info("no new glofas file to process!")
        sys.exit()

    # load watersheds data
    watersheds = watersheds_gdb_reader()
    for data_date in new_files:
        logging.info("processing GLoFAS: " + data_date)
        fixed_sites = os.path.join(GLOFAS_PROC_DIR, "threspoints_" + data_date + ".txt")
        dyn_sites = os.path.join(
            GLOFAS_PROC_DIR, "threspointsDyn_" + data_date + ".txt"
        )
        # read fixed station data
        header_fixed_19 = [
            "Point No",
            "ID",
            "Basin",
            "Location",
            "Station",
            "Country",
            "Continent",
            "Country_code",
            "Upstream area",
            "unknown_1",
            "Lon",
            "Lat",
            "empty",
            "unknown_2",
            "Days_until_peak",
            "GloFAS_2yr",
            "GloFAS_5yr",
            "GloFAS_20yr",
            "Alert_level",
        ]
        header_fixed_18 = [
            "Point No",
            "ID",
            "Basin",
            "Location",
            "Station",
            "Country",
            "Continent",
            "Country_code",
            "Upstream area",
            "Lon",
            "Lat",
            "empty",
            "unknown_2",
            "Days_until_peak",
            "GloFAS_2yr",
            "GloFAS_5yr",
            "GloFAS_20yr",
            "Alert_level",
        ]
        fixed_data = pd.read_csv(fixed_sites, header=None, on_bad_lines="skip")
        fixed_data_col = len(fixed_data.axes[1])
        if fixed_data_col == 19:
            fixed_data.columns = header_fixed_19
        elif fixed_data_col == 18:
            fixed_data.columns = header_fixed_18
        # read dynamic station data
        header_dyn_19 = [
            "Point No",
            "ID",
            "Station",
            "Basin",
            "Location",
            "Country",
            "Continent",
            "Country_code",
            "unknown_1",
            "Upstream area",
            "Lon",
            "Lat",
            "empty",
            "unknown_2",
            "Days_until_peak",
            "GloFAS_2yr",
            "GloFAS_5yr",
            "GloFAS_20yr",
            "Alert_level",
        ]
        header_dyn_18 = [
            "Point No",
            "ID",
            "Station",
            "Basin",
            "Location",
            "Country",
            "Continent",
            "Country_code",
            "Upstream area",
            "Lon",
            "Lat",
            "empty",
            "unknown_2",
            "Days_until_peak",
            "GloFAS_2yr",
            "GloFAS_5yr",
            "GloFAS_20yr",
            "Alert_level",
        ]
        dyn_data = pd.read_csv(dyn_sites, header=None, on_bad_lines="skip")
        dyn_data_col = len(dyn_data.axes[1])
        if dyn_data_col == 19:
            dyn_data.columns = header_dyn_19
        elif dyn_data_col == 18:
            dyn_data.columns = header_dyn_18
        # merge two datasets
        if fixed_data_col == dyn_data_col:
            total_data = fixed_data.append(dyn_data, sort=True)
        else:
            total_data = fixed_data
            print("dyn_data is ignored")

        # create a geopanda dataset
        gdf = geopandas.GeoDataFrame(
            total_data,
            geometry=geopandas.points_from_xy(total_data.Lon, total_data.Lat),
        )
        gdf.crs = "EPSG:4326"
        # generate sindex
        gdf.sindex

        # sjoin
        gdf_watersheds = geopandas.sjoin(gdf, watersheds, op="within")
        gdf_watersheds.rename(columns={"index_right": "pfaf_id"}, inplace=True)

        forcast_time = (fixed_sites.split("_")[1]).replace("00.txt", "")
        forcast_time = datetime.strptime(forcast_time, "%Y%m%d")
        # add column "Forecast Date"
        gdf_watersheds["Forecast Date"] = forcast_time.isoformat()

        # convert "GloFAS_2yr","GloFAS_5yr","GloFAS_20y" to 0~100
        if gdf_watersheds["GloFAS_2yr"].max() <= 1.0:
            gdf_watersheds["GloFAS_2yr"] = gdf_watersheds["GloFAS_2yr"] * 100
            gdf_watersheds["GloFAS_5yr"] = gdf_watersheds["GloFAS_5yr"] * 100
            gdf_watersheds["GloFAS_20yr"] = gdf_watersheds["GloFAS_20yr"] * 100
        gdf_watersheds = gdf_watersheds.astype(
            {"GloFAS_2yr": int, "GloFAS_5yr": int, "GloFAS_20yr": int}
        )

        # fill max_EPS
        gdf_watersheds["max_EPS"] = gdf_watersheds.apply(
            lambda row: str(row["GloFAS_2yr"])
            + "/"
            + str(row["GloFAS_5yr"])
            + "/"
            + str(row["GloFAS_20yr"]),
            axis=1,
        )

        # write out csv file
        out_csv = os.path.join(GLOFAS_DIR, "threspoints_" + data_date + ".csv")
        out_columns = [
            "Point No",
            "Station",
            "Basin",
            "Country",
            "Lat",
            "Lon",
            "Upstream area",
            "Forecast Date",
            "max_EPS",
            "GloFAS_2yr",
            "GloFAS_5yr",
            "GloFAS_20yr",
            "Alert_level",
            "Days_until_peak",
            "pfaf_id",
        ]
        gdf_watersheds.to_csv(
            out_csv, index=False, columns=out_columns, float_format="%.3f"
        )

        logging.info("generated: " + out_csv)

        # write to excel
        # out_excel = glofasdata + "threspoints_" + data_date + ".xlsx"
        # gdf_watersheds.to_excel(out_excel,index=False,columns=out_columns,sheet_name='Sheet_name_1')

        # to geojson
        out_geojson = os.path.join(GLOFAS_DIR, "threspoints_" + data_date + ".geojson")
        gdf_watersheds.to_file(out_geojson, driver="GeoJSON")

    # return a list date to be processed with GFMS
    return new_files


def GFMS_download(bin_file):
    """download a given bin file"""

    # find download url
    datestr = bin_file.split("_")[2]
    baseurl = config.get("gfms", "HOST")
    dataurl = os.path.join(baseurl, datestr[:4], datestr[:6])
    download_data_url = os.path.join(dataurl, bin_file)

    # check if it download
    binfile_local = os.path.join(GFMS_PROC_DIR, bin_file)
    # check if the size is ok
    if os.path.exists(binfile_local):
        binsize = os.path.getsize(binfile_local)
        if binsize < 7000000:
            os.remove(binfile_local)

    if not os.path.exists(binfile_local):
        # download the data
        try:
            r = requests.get(download_data_url, allow_redirects=True)
        except requests.exceptions.HTTPError as e:
            logging.error("Downlaod failed: " + e.response.text)
            sys.exit()

        open(binfile_local, "wb").write(r.content)
        logging.info("Download: " + bin_file)

    # generate header file
    hdr_header = """NCOLS 2458
    NROWS 800
    XLLCORNER -127.25
    YLLCORNER -50    print(lastest_csv)

    CELLSIZE 0.125
    PIXELTYPE FLOAT
    BYTEORDER LSBFIRST
    NODATA_VALUE -9999
    """
    header_file = binfile_local.replace(".bin", ".hdr")
    with open(header_file, "w") as f:
        f.write(hdr_header)

    # generate vrt file
    vrt_template = """<VRTDataset rasterXSize="4916" rasterYSize="1600" subClass="VRTWarpedDataset">
  <GeoTransform> -1.2725000000000000e+02,  6.2500000000000000e-02,  0.0000000000000000e+00,  5.0000000000000000e+01,  0.0000000000000000e+00, -6.2500000000000000e-02</GeoTransform>
  <VRTRasterBand dataType="Float32" band="1" subClass="VRTWarpedRasterBand">
    <NoDataValue>-9999</NoDataValue>
  </VRTRasterBand>
  <BlockXSize>512</BlockXSize>
  <BlockYSize>128</BlockYSize>
  <GDALWarpOptions>
    <WarpMemoryLimit>6.71089e+07</WarpMemoryLimit>
    <ResampleAlg>NearestNeighbour</ResampleAlg>
    <WorkingDataType>Float32</WorkingDataType>
    <Option name="INIT_DEST">NO_DATA</Option>
    <SourceDataset relativeToVRT="1">{}</SourceDataset>
    <Transformer>
      <ApproxTransformer>
        <MaxError>0.125</MaxError>
        <BaseTransformer>
          <GenImgProjTransformer>
            <SrcGeoTransform>-127.25,0.125,0,50,0,-0.125</SrcGeoTransform>
            <SrcInvGeoTransform>1018,8,0,400,0,-8</SrcInvGeoTransform>
            <DstGeoTransform>-127.25,0.0625,0,50,0,-0.0625</DstGeoTransform>
            <DstInvGeoTransform>2036,16,0,800,0,-16</DstInvGeoTransform>
          </GenImgProjTransformer>
        </BaseTransformer>
      </ApproxTransformer>
    </Transformer>
    <BandList>
      <BandMapping src="1" dst="1">
        <SrcNoDataReal>-9999</SrcNoDataReal>
        <SrcNoDataImag>0</SrcNoDataImag>
        <DstNoDataReal>-9999</DstNoDataReal>
        <DstNoDataImag>0</DstNoDataImag>
      </BandMapping>
    </BandList>
  </GDALWarpOptions>
</VRTDataset>"""

    # generate VRT file
    vrt_file = binfile_local.replace(".bin", ".vrt")
    with open(vrt_file, "w") as f:
        f.write(vrt_template.format(bin_file))

    return vrt_file
    print(lastest_csv)


def GFMS_extract_by_mask(vrt_file, mask_json):
    """extract data for a single watershed"""

    # print(vrt_file)
    # print(mask_json['features'][0]['geometry'])

    with rasterio.open(vrt_file) as src:
        try:
            out_image, out_transform = mask(
                src, [mask_json["features"][0]["geometry"]], crop=True
            )
        except rasterio.errors.RasterioIOError as er:
            logging.warning("RasterioIOError:" + vrt_file)
            src = None
            return pd.DataFrame()
        except ValueError as e:
            #'Input shapes do not overlap raster.'
            # print(e)
            src = None
            # return empty dataframe    print(lastest_csv)
            return pd.DataFrame()

    # extract data
    no_data = src.nodata
    # extract the values of the masked array
    # print(out_image)
    data = out_image[0]
    # extract the row, columns of the valid values
    row, col = np.where(data != no_data)
    point_value = np.extract(data != no_data, data)
    if len(point_value) == 0:
        src = None
        # return empty dataframe
        return pd.DataFrame()

    T1 = out_transform * Affine.translation(0.5, 0.5)  # reference the pixel centre
    # rc2xy = lambda r, c: (c, r) * T1
    rc2xy = lambda r, c: T1 * (c, r)
    px, py = src.res
    # print (px,py)
    pixel_area_km2 = (
        lambda lon, lat: 111.111 * 111.111 * math.cos(lat * 0.01745) * px * py
    )
    d = geopandas.GeoDataFrame({"col": col, "row": row, "intensity": point_value})
    # coordinate transformation
    d["lon"] = d.apply(lambda row: rc2xy(row.row, row.col)[0], axis=1)
    d["lat"] = d.apply(lambda row: rc2xy(row.row, row.col)[1], axis=1)
    d["area"] = d.apply(lambda row: pixel_area_km2(row.lon, row.lat), axis=1)

    # geometry
    d["geometry"] = d.apply(lambda row: Point(row["lon"], row["lat"]), axis=1)
    # first 2 points
    src = None
    return d


def GFMS_extract_by_watershed(vrt_file):
    """extract and summary"""

    # load watersheds data
    watersheds = watersheds_gdb_reader()
    pfaf_id_list = watersheds.index.tolist()

    # setup output file
    headers_list = [
        "pfaf_id",
        "GFMS_TotalArea_km",
        "GFMS_perc_Area",
        "GFMS_MeanDepth",
        "GFMS_MaxDepth",
        "GFMS_Duration",
    ]
    # put summary file into proc folder before fix-duration
    summary_file = os.path.join(GFMS_PROC_DIR, os.path.basename(vrt_file)[:-4] + ".csv")
    if not os.path.exists(summary_file):
        with open(summary_file, "w") as f:
            writer = csv.writer(f)
            writer.writerow(headers_list)
    else:
        # already processed,
        return

    # write out the summary
    # count = 0
    with open(summary_file, "a") as f:
        writer = csv.writer(f)

        for pfaf_id in pfaf_id_list:
            # for command line mode
            # count += 1
            # progress(count,  len(pfaf_id_list), status='pfaf_id')

            test_json = json.loads(
                geopandas.GeoSeries([watersheds.loc[pfaf_id, "geometry"]]).to_json()
            )
            # plot check
            data_points = GFMS_extract_by_mask(vrt_file, test_json)

            # write summary to a csv file
            GFMS_Duration = 0
            if not data_points.empty:
                GFMS_TotalArea = data_points["area"].sum()
                if GFMS_TotalArea > 100.0:
                    GFMS_Duration = 3
                GFMS_Area_percent = (
                    GFMS_TotalArea / watersheds.loc[pfaf_id]["area_km2"] * 100
                )
                GFMS_MeanDepth = data_points["intensity"].mean()
                GFMS_MaxDepth = data_points["intensity"].max()
            else:
                GFMS_TotalArea = 0.0
                GFMS_Area_percent = 0.0
                GFMS_MeanDepth = 0.0
                GFMS_MaxDepth = 0.0
                GFMS_Duration = 0

            results_list = [
                pfaf_id,
                GFMS_TotalArea,
                GFMS_Area_percent,
                GFMS_MeanDepth,
                GFMS_MaxDepth,
                GFMS_Duration,
            ]
            writer.writerow(results_list)

    logging.info("generated: " + summary_file)

    return


def GFMS_data_extractor(bin_file):
    """extract data from a given binfile"""

    # download GFMS binfile, generate vrt file
    vrt_file = GFMS_download(bin_file)

    # extract data by watershed
    logging.info("processing: " + vrt_file)
    GFMS_extract_by_watershed(vrt_file)

    # generate tiff from bin file
    tiff_name = os.path.basename(vrt_file).replace(".vrt", ".tiff")
    tiff_file = os.path.join(GFMS_IMG_DIR, tiff_name)
    gdalcmd = f"gdal_translate -co TILED=YES -co COMPRESS=LZW -of GTiff {vrt_file} {tiff_file}"
    os.system(gdalcmd)
    logging.info("generated: " + tiff_file)

    return


def GFMS_fix_duration(csv0, csvlist):
    """fix duration"""
    # notice the folder issue
    # base0 shall be in GFMS_SUM_DIR
    # unfixed are in GFMS_PROC_DIR

    # first check if csv0 exists
    basecsv = os.path.join(GFMS_SUM_DIR, csv0)
    if os.path.exists(basecsv):
        df0 = pd.read_csv(basecsv)
        start_in = 0
    else:
        df0 = pd.read_csv(os.path.join(GFMS_PROC_DIR, csvlist[0]))
        start_in = 1
        # also write out to SUM folder
        df0.to_csv(os.path.join(GFMS_SUM_DIR, csvlist[0]), index=False)

    for name in csvlist[start_in:]:
        csv_file = os.path.join(GFMS_PROC_DIR, name)
        df = pd.read_csv(csv_file)
        df["GFMS_Duration0"] = df["pfaf_id"].map(
            df0.set_index("pfaf_id")["GFMS_Duration"]
        )
        df["GFMS_Duration"] = df.apply(
            lambda row: 3 + int(row.GFMS_Duration0)
            if (row.GFMS_TotalArea_km > 100.0)
            else 0,
            axis=1,
        )
        del df["GFMS_Duration0"]
        fix_csv = os.path.join(GFMS_SUM_DIR, name)
        df.to_csv(fix_csv, index=False)
        logging.info("generated: " + fix_csv)
        df0 = None
        df0 = df
        df = None


def GFMS_processing(proc_dates_list):
    """process GFMS data with a given list of dates"""

    binhours = ["00", "03", "06", "09", "12", "15", "18", "21"]
    for data_date in proc_dates_list:
        real_date = data_date[:-2]
        for binhour in binhours:
            bin_file = "Flood_byStor_" + real_date + binhour + ".bin"
            # process bin file
            GFMS_data_extractor(bin_file)

        # run duration caculation
        # find the previous one, previous day 21 hour
        previous_date = datetime.strptime(real_date, "%Y%m%d") - timedelta(days=1)
        base0 = "Flood_byStor_" + previous_date.strftime("%Y%m%d") + "21.csv"
        fix_list = ["Flood_byStor_" + real_date + x + ".csv" for x in binhours]
        # call fix duration
        GFMS_fix_duration(base0, fix_list)

        # flood severity calculation
        gfmscsv = os.path.join(GFMS_SUM_DIR, "Flood_byStor_" + data_date + ".csv")
        glofascsv = os.path.join(GLOFAS_DIR, "threspoints_" + data_date + ".csv")

        # in case of glofascsv data is missing, use the latest
        if not os.path.exists(glofascsv):
            glofas_latest = findLatest(GLOFAS_DIR, "csv")
            glofascsv = os.path.join(GLOFAS_DIR, glofas_latest)

        flood_severity(gfmscsv, glofascsv, real_date)

        # zip GFMS data after processing
        curdir = os.getcwd()
        os.chdir(GFMS_PROC_DIR)
        zipcmd = "zip gfms_{adate}.zip Flood_byStor_{adate}*.*".format(adate=real_date)
        os.system(zipcmd)
        logging.info("generated: " + f"Flood_byStor_{real_date}.zip")
        # remove all the file
        fileList = glob.glob("Flood_byStor_{adate}*.*".format(adate=real_date))
        for filePath in fileList:
            try:
                os.remove(filePath)
            except:
                logging.warning("Error while deleting file : ", filePath)
        os.chdir(curdir)

    return


def GFMS_cron():
    """run GFMS cron job"""

    # process GloFAS data
    processing_dates = GloFAS_process()
    # process GFMS data
    # processing_dates = ['2021120200']
    GFMS_processing(processing_dates)

    # check if today's date are generated
    # if now hwrf data, then generate the output for 00 hour
    hwrf_flag = hwrf_today()
    if hwrf_flag:
        return
    # otherwise
    today = date.today()
    tstr = today.strftime("%Y%m%d")
    tstr = tstr + "00"
    gfmscsv = os.path.join(GFMS_SUM_DIR, "Flood_byStor_" + tstr + ".csv")
    glofascsv = os.path.join(GLOFAS_DIR, "threspoints_" + tstr + ".csv")
    if os.path.exists(gfmscsv) and os.path.exists(glofascsv):
        logging.info("no hwrf: " + tstr + " generating ...")
        # update_HWRF_MoM(tstr)
        # update_HWRFMoM_DFO_VIIRS(tstr)
        # final_alert_pdc(tstr)
        hwrf_workflow(tstr)


def GFMS_fixdate(adate):
    """run cron job"""
    # cron steup cd ~/ModelofModels/data && python datatool.py --cron
    # run every three hours
    # edit: crontab -e
    # 5 0,3,6,9,12,15,18,21 * * * commnad

    # it is likly only one date: 2020051600
    # processing_dates = GloFAS_process()
    # check if GMS data is available
    # processing_dates = ['2020061800','2020061900','2020062000']
    if len(adate) == 8:
        adate = adate + "00"
    processing_dates = [adate]
    binhours = ["00", "03", "06", "09", "12", "15", "18", "21"]
    for data_date in processing_dates:
        real_date = data_date[:-2]
        for binhour in binhours:
            # bin_file = "Flood_byStor_" + real_date + binhour + ".bin"
            summary_file = "Flood_byStor_{}.csv".format(real_date + binhour)
            summary_file = os.path.join(GFMS_SUM_DIR, summary_file)
            # remove partial processed summary file
            if os.path.exists(summary_file):
                os.remove(summary_file)
            # also need remove the file processing folder
            csv_in_proc = "Flood_byStor_{}.csv".format(real_date + binhour)
            csv_in_proc = os.path.join(GFMS_PROC_DIR, csv_in_proc)
            if os.path.exists(csv_in_proc):
                os.remove(csv_in_proc)
    # reprocessing file
    GFMS_processing(processing_dates)


def debug():
    """debug the function"""
    # issue 38: gfms broken bin file
    binfile = "Flood_byStor_2022103103.bin"
    GFMS_data_extractor(binfile)


def main():
    """run the cron job"""
    GFMS_cron()


if __name__ == "__main__":
    main()
