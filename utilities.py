'''
utilities.py
routines shared across the modules

'''

import os, glob
import settings
import pandas as pd
import geopandas 
from datetime import date,timedelta,datetime

def watersheds_gdb_reader():
    """reader watersheds gdb into geopandas"""
    
    # pfaf_id, areakm2
    watersheds = geopandas.read_file(settings.WATERSHED_SHP)
    # issue #1
    # some old code use aqid, need to be updated
    #watersheds.rename(columns={"pfaf_id": "aqid"},inplace=True)
    #watersheds.set_index("aqid",inplace=True)
    watersheds.set_index("pfaf_id",inplace=True) 
    watersheds.crs = "EPSG:4326"

    return watersheds


def read_data(datafile):
    df = pd.read_csv(datafile)
    #df = pd.DataFrame(df)
    return df

def from_today(adate):
    # conver adate to date object
    # adate may come in as YYYYMMDD
    da = datetime.strptime(adate[:8],"%Y%m%d").date()
    today = date.today()
    delta = da - today

    return delta.days

def hour_diff(adate1,adate2):
    """find the hour difference bewteen to date string"""
    # data format YYYYMMDDHH
    da1 = datetime.strptime(adate1,"%Y%m%d%H")
    da2 = datetime.strptime(adate2,"%Y%m%d%H")
    delta = da1 - da2
    dhours = int(delta.total_seconds() / 3600)
    return dhours

def findLatest(apath, atype):
    """return the latest file in folder"""
    check_path = os.path.join(apath,f"*.{atype}")
    all_files = glob.glob(check_path)
    latest_file = max(all_files, key=os.path.getctime)
    
    return os.path.basename(latest_file)    

def main():
    ''' test routines'''

    watershed = watersheds_gdb_reader()
    print(watershed.head)

    # test from today function
    adate = date.today().strftime("%Y%m%d")
    ddays = from_today(adate)
    print("{} => {}".format(adate,ddays))

    yesterday = date.today() - timedelta(days = 2)
    adate = yesterday.strftime("%Y%m%d")
    ddays = from_today(adate)
    print("{} => {}".format(adate,ddays))

    adate = adate + "18"
    ddays = from_today(adate)
    print("{} => {}".format(adate,ddays))
    
    # test hour_diff
    da1 = "2022100910"
    da2 = "2022100918"
    dhours = hour_diff(da1,da2)
    print("{} - {} = {} hours".format(da1,da2,dhours))

    da1 = "2022100910"
    da2 = "2022100818"
    dhours = hour_diff(da1,da2)
    print("{} - {} = {} hours".format(da1,da2,dhours))

    lastest_csv = findLatest(settings.GLOFAS_SUM_DIR,"csv")
    print(lastest_csv)

if __name__ == '__main__':
    main()
