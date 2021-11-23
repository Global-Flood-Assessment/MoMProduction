"""
GFMS_tool.py

Download and process GFMS and GloFAS data

Two main function:
    * GFMS_cron : run the daily cron job
    * GFMS_cron_fix: rerun cron-job for a given date
"""

import os
import logging

from settings import *

def GloFAS_download():
    """download glofas data from ftp"""
    ftpsite = {}
    ftpsite['host'] = config.get('glofas','HOST')
    ftpsite['user'] = config.get('glofas','USER')
    ftpsite['passwd'] = config.get('glofas','PASSWD')
    ftpsite['directory'] = config.get('glofas','DIRECTORY')
    from ftplib import FTP
    ftp = FTP(host=ftpsite['host'],user=ftpsite['user'],passwd=ftpsite['passwd'])
    ftp.cwd(ftpsite['directory'])
    file_list = ftp.nlst()
    job_list = []
    for txt in file_list:
        save_txt = os.path.join(glofas_dir,txt)
        if os.path.exists(save_txt):
            continue
        with open(save_txt, 'wb') as fp:
            ftp.retrbinary('RETR '+txt, fp.write)
            if ("threspoints_"  in txt):
                job_list.append((txt.split(".")[0]).replace("threspoints_",""))
    ftp.quit()
    
    return job_list

def GloFAS_process():
    """process glofas data"""
    new_files = GloFAS_download()
    print(new_files)

    return

def GFMS_cron():
    """ run GFMS cron job"""

    processing_dates = GloFAS_process()

def main():
    """test code"""
    GFMS_cron()

if __name__ == "__main__":
    main()
