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

def generate_procesing_list():
    """ generate list of date to process"""
    hosturl = config.get('dfo','HOST')
    cur_year  = date.today().year
    hosturl = os.path.join(hosturl,str(cur_year))
    reqs = requests.get(hosturl)
    soup = BeautifulSoup(reqs.text,"html.parser")
    
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

def DFO_cron():
    """cron job to process DFO"""

    datelist = generate_procesing_list()
    if len(datelist) == 0:
        logging.info("no new data to process!")
        sys.exit(0)    
    
    print(datelist)
    
    return

def main():
    DFO_cron()

if __name__ == "__main__":
    main()