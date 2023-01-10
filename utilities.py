"""
utilities.py
routines shared across the modules

"""

import glob
import os
from datetime import date, datetime, timedelta

import geopandas
import pandas as pd
import requests

import settings


def watersheds_gdb_reader():
    """reader watersheds gdb into geopandas"""

    # pfaf_id, areakm2
    watersheds = geopandas.read_file(settings.WATERSHED_SHP)
    # issue #1
    # some old code use aqid, need to be updated
    # watersheds.rename(columns={"pfaf_id": "aqid"},inplace=True)
    # watersheds.set_index("aqid",inplace=True)
    watersheds.set_index("pfaf_id", inplace=True)
    watersheds.crs = "EPSG:4326"

    return watersheds


def read_data(datafile):
    df = pd.read_csv(datafile)
    # df = pd.DataFrame(df)
    return df


def from_today(adate):
    # conver adate to date object
    # adate may come in as YYYYMMDD
    da = datetime.strptime(adate[:8], "%Y%m%d").date()
    today = date.today()
    delta = da - today

    return delta.days


def hour_diff(adate1, adate2):
    """find the hour difference bewteen to date string"""
    # data format YYYYMMDDHH
    da1 = datetime.strptime(adate1, "%Y%m%d%H")
    da2 = datetime.strptime(adate2, "%Y%m%d%H")
    delta = da1 - da2
    dhours = int(delta.total_seconds() / 3600)
    return dhours


def findLatest(apath, atype):
    """return the latest file in folder"""
    check_path = os.path.join(apath, f"*.{atype}")
    all_files = glob.glob(check_path)
    # latest_file = max(all_files, key=os.path.getctime)
    try:
        latest_file = max(all_files)
    except ValueError:
        return ""

    return os.path.basename(latest_file)


def get_latestitems(afolder, numofitems=7):
    """get the list of the latest items in a folder"""

    items = sorted(os.listdir(afolder))

    if len(items) < numofitems:
        return items
    else:
        return items[-numofitems:]


def url_exits(aurl):
    """test if a url exists"""
    req = requests.get(aurl)
    if req.status_code == 200:
        return True
    else:
        return False


def hwrf_today(adate="", ahour=""):
    """check if hwrf has date for today"""
    tstr, hstr = adate, ahour
    if tstr == "":
        today = date.today()
        tstr = today.strftime("%Y%m%d")

    if hstr == "":
        hstr = "00"

    hosturl = settings.config.get("hwrf", "HOST")
    turl = os.path.join(hosturl, "hwrf.{}".format(tstr), hstr)
    # print(turl)
    has_data = url_exits(turl)
    return has_data

def get_current_processing_datehour(time_delay = 6):
    """get the current processing datehour with a time-delay
         -- time_delay(in hours)
         -- return YYYYMMDDHH (hour in 00, 06, 12, 18)
    """
    # get current time
    ct = datetime.now()
    dt = ct - timedelta(hours = time_delay)
    # integer division
    ahour = (dt.hour // 6) * 6
    adatestr = dt.strftime("%Y%m%d") + str(ahour).zfill(2)
    return adatestr

def main():
    """test routines"""

    print("==> read watershed")
    watershed = watersheds_gdb_reader()
    print(watershed.head)

    # test from today function
    print("==> from tdoay")
    adate = date.today().strftime("%Y%m%d")
    ddays = from_today(adate)
    print("{} => {}".format(adate, ddays))

    yesterday = date.today() - timedelta(days=2)
    adate = yesterday.strftime("%Y%m%d")
    ddays = from_today(adate)
    print("{} => {}".format(adate, ddays))

    adate = adate + "18"
    ddays = from_today(adate)
    print("{} => {}".format(adate, ddays))

    # test hour_diff
    print("==> hour diff")
    da1 = "2022100910"
    da2 = "2022100918"
    dhours = hour_diff(da1, da2)
    print("{} - {} = {} hours".format(da1, da2, dhours))

    da1 = "2022100910"
    da2 = "2022100818"
    dhours = hour_diff(da1, da2)
    print("{} - {} = {} hours".format(da1, da2, dhours))

    print("==> find latest")
    lastest_csv = findLatest(settings.GLOFAS_SUM_DIR, "csv")
    print(lastest_csv)

    print("==> get lastest items")
    lastest_items = get_latestitems(settings.HWRF_PROC_DIR)
    print(lastest_items)
    lastest_items = get_latestitems(settings.HWRF_SUM_DIR, numofitems=5)
    print(lastest_items)

    print("==> url exist")
    today = date.today()
    tstr = today.strftime("%Y%m%d")
    aurl = f"https://ftpprd.ncep.noaa.gov/data/nccf/com/hwrf/prod/hwrf.{tstr}/00/"
    print("HWRF today: ")
    print(aurl, ":", url_exits(aurl))
    ereyesterday = today - timedelta(days=2)
    tstr = ereyesterday.strftime("%Y%m%d")
    print("HWRF the day before yesterday")
    aurl = f"https://ftpprd.ncep.noaa.gov/data/nccf/com/hwrf/prod/hwrf.{tstr}/00/"
    print(aurl, ":", url_exits(aurl))

    print("==> hwrf today")
    print("hwrf has the data today: ", hwrf_today())
    print("hwrf has the data today: ", hwrf_today(ahour="06"))
    print("hwrf has the data today: ", hwrf_today(adate="20221111", ahour="00"))
    print("hwrf has the data today: ", hwrf_today(adate="20221111", ahour="06"))

    print("==> get current processing datehour")
    print("current time: ", datetime.now())
    print("current processing datehour: ", get_current_processing_datehour())
    print("current processing datehour with 3 hour delay: ", get_current_processing_datehour(time_delay=3))

if __name__ == "__main__":
    main()
