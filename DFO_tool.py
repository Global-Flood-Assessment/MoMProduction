"""
DFO_tool.py

Download and process DFO data

Two main function:
    * DFO_cron : run the daily cron job
    * DFO_cron_fix: rerun cron-job for a given date
"""


import sys, os, shutil
from datetime import date
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import subprocess

from settings import *

def get_real_date(year,day_num):
    """ get the real date"""
    
    #allData/61/MCDWD_L3_NRT/2021/021

    #year,day_num = foldername.split("/")[-2:]
    res = datetime.strptime(str(year) + "-" + str(day_num), "%Y-%j").strftime("%Y%m%d")

    return res

def check_status(adate):
    """ check if a give date is processed"""

    processed_list = os.listdir(DFO_SUM_DIR)
    processed = any(adate in x for x in processed_list)
    
    return processed

def get_hosturl():
    """ get the host url"""
    baseurl = config.get('dfo','HOST')
    cur_year  = date.today().year
    hosturl = os.path.join(baseurl,str(cur_year))
    
    return hosturl

def generate_procesing_list():
    """ generate list of date to process"""
    hosturl = get_hosturl()   
    reqs = requests.get(hosturl)
    soup = BeautifulSoup(reqs.text,"html.parser")
    
    cur_year = hosturl[-4:]
    datelist = {}
    for link in soup.find_all('a'):
        day_num = link.string
        if not day_num.isdigit():
            continue
        real_date = get_real_date(cur_year,day_num)
        if check_status(real_date):
            continue
        datelist[day_num]=real_date

    return datelist

def dfo_download(subfolder):
    """ download a subfolder """

    # check if there is unfinished download
    d_dir = os.path.join(DFO_PROC_DIR,subfolder)
    if os.path.exists(d_dir):
        # is file cases
        if os.path.isfile(d_dir):
            os.remove(d_dir)
        else:
            # remove the subfolder
            shutil.rmtree(d_dir)   

    dfokey = config.get('dfo','TOKEN')
    dataurl = os.path.join(get_hosturl(), subfolder)
    wgetcmd = 'wget -r --no-parent -R .html,.tmp -nH -l1 --cut-dirs=8 {dataurl} --header "Authorization: Bearer {key}" -P {downloadfolder}'
    wgetcmd = wgetcmd.format(dataurl = dataurl,key=dfokey,downloadfolder=DFO_PROC_DIR)
    #print(wgetcmd)
    exitcode = subprocess.call(wgetcmd, shell=True)
    if not exitcode == 0:
        #something wrong with downloading
        logging.warning("download failed: " + dataurl)
        sys.exit()

    return

def DFO_cron():
    """cron job to process DFO"""

    datelist = generate_procesing_list()
    if len(datelist) == 0:
        logging.info("no new data to process!")
        sys.exit(0)    
    
    for key in datelist:
        logging.info("download: " + key)
        dfo_download(key)
        logging.info("download finished!")
    
    return

def main():
    DFO_cron()

if __name__ == "__main__":
    main()