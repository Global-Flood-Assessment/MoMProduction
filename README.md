# ModelofModels Production
The following guide is tested on Ubuntu 18.04 and 20.04 LTS.  
The current testing VM is a m1.small instance on [Jetstream cloud](https://portal.xsede.org/jetstream) with 2 vcpus, 4GB memory, 20GB storage with an extra 100GB volume attached.   

**Note**: A non-administrator user "tester" in Ubuntu is used this guide. Please update the path in cron-job examples with the right user name for your installation. 

## 0. Timezone setup
Upstream data are produced by agencies across the world, UTC time zone is recommended.  
In Ubuntu, set timezone to UTC: 
```
sudo timedatectl set-timezone UTC
```
And run "timedatectl" to check: 
```
                      Local time: Mon 2022-04-04 01:45:14 UTC
                  Universal time: Mon 2022-04-04 01:45:14 UTC
                        RTC time: Mon 2022-04-04 01:45:14
                       Time zone: UTC (UTC, +0000)
       System clock synchronized: yes
systemd-timesyncd.service active: yes
                 RTC in local TZ: no
```
## 1. Setup Python environment
### 1.1 Install Python
Python version tested: 3.8, 3.9    
[Miniconda](https://docs.conda.io/en/latest/miniconda.html) is recommended.  
Latest release: [Miniconda3 Linux 64-bit](https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh) 
### 1.2 Enable conda-forge channel
After miniconda installed, the commands enable conda-forge channel  
```
conda config --add channels conda-forge
conda config --set channel_priority strict
conda config --show channels
```
### 1.2 Clone MoMProduction repo:
```
git clone https://github.com/Global-Flood-Assessment/MoMProduction.git
```
### 1.3 Install Python Packages
Install packages by creating an environment 'mom'.
```
conda create --name mom --file packagelist.txt
conda activate mom
```
All the python commands after this part are running in this environment.  
### 1.3 Other software requirements
Check if zip, wget, gdal are installed.  
Install the packages if not available:
```
sudo apt install gdal-bin 
```
## 2. Initialize the setup
Please copy [sample_production.cfg](https://github.com/Global-Flood-Assessment/MoMProduction/blob/main/sample_production.cfg) to **production.cfg**, or run initialize.py, it will do the copy.  
Check production.cfg: 
- in general section, change WORKING_DIR (base directory for downloading and processing data) and PRODUCT_DIR (base directory for the data products) if necessary;
- in glofas section, fill in user/passwd for ftp site;  
- in dfo section, fill in token for download [more on Automating NRT Downloads](https://nrt4.modaps.eosdis.nasa.gov/archive/allData/61)  
```
[general]
WORKING_DIR: ~/MoM/Processing
PRODUCT_DIR: ~/MoM/Products

[glofas]
HOST: data-portal.ecmwf.int
USER: ???
PASSWD: ???
DIRECTORY: /for_PDC

[dfo]
TOKEN: ???
```
Initialize the production setup: 
```
python initialize.py
```
It performs the following tasks:   
- create the folder structures defined in production.cfg
- check username/password, token in production.cfg
- unzip watershed.shp 

## 3. Test run
All the processing jobs can be tested in the following orders. It may take several hours to finish, it produces data products from the latest several days.
```
python MoM_run.py -j GFMS
python MoM_run.py -j HWRF
python MoM_run.py -j DFO
python MoM_run.py -j VIIRS
```
The outputs to the console are very minimal, the progress can be checked through the log file under processing/logs folder. The log is generated each month, e.g 2021_11.log, 2021_12.log. 
```
sample log output
2021-12-09 10:39:18,174 - MoM_run - INFO : run GFMS
2021-12-09 10:39:33,055 - GFMS_tool - INFO : processing GLoFAS: 2021120200
2021-12-09 10:39:34,705 - GFMS_tool - INFO : generated: Products/GLOFAS/threspoints_2021120200.csv
2021-12-09 10:39:35,313 - GFMS_tool - INFO : processing GLoFAS: 2021120300
2021-12-09 10:39:36,909 - GFMS_tool - INFO : generated: Products/GLOFAS/threspoints_2021120300.csv
2021-12-09 10:39:37,514 - GFMS_tool - INFO : processing GLoFAS: 2021120400
2021-12-09 10:39:39,112 - GFMS_tool - INFO : generated: Products/GLOFAS/threspoints_2021120400.csv
2021-12-09 10:39:39,714 - GFMS_tool - INFO : processing GLoFAS: 2021120500
2021-12-09 10:39:41,349 - GFMS_tool - INFO : generated: Products/GLOFAS/threspoints_2021120500.csv
2021-12-09 10:39:41,952 - GFMS_tool - INFO : processing GLoFAS: 2021120600
2021-12-09 10:39:43,555 - GFMS_tool - INFO : generated: Products/GLOFAS/threspoints_2021120600.csv
2021-12-09 10:39:44,166 - GFMS_tool - INFO : processing GLoFAS: 2021120700
2021-12-09 10:39:45,781 - GFMS_tool - INFO : generated: Products/GLOFAS/threspoints_2021120700.csv
2021-12-09 10:39:46,389 - GFMS_tool - INFO : processing GLoFAS: 2021120800
2021-12-09 10:39:48,042 - GFMS_tool - INFO : generated: Products/GLOFAS/threspoints_2021120800.csv
2021-12-09 10:39:48,677 - GFMS_tool - INFO : processing GLoFAS: 2021120900
2021-12-09 10:39:50,289 - GFMS_tool - INFO : generated: Products/GLOFAS/threspoints_2021120900.csv
2021-12-09 10:39:53,383 - GFMS_tool - INFO : Download: Flood_byStor_2021120200.bin
2021-12-09 10:39:53,385 - GFMS_tool - INFO : processing: Processing/gfms/Flood_byStor_2021120200.vrt
2021-12-09 10:41:43,808 - GFMS_tool - INFO : generated: Processing/gfms/Flood_byStor_2021120200.csv
2021-12-09 10:41:44,154 - GFMS_tool - INFO : generated: Products/GFMS/GFMS_image/Flood_byStor_2021120200.tiff
2021-12-09 10:41:47,233 - GFMS_tool - INFO : Download: Flood_byStor_2021120203.bin
...
```   
## 4. Setup cron jobs
Each datasets are released in difference schedules, GloFAS, DFO, VIIRS are released once a day; GFMS are the predication data in 3-hour interval and available in advance, amd are processed along with GloFAS data. HWRF is updated every 6 six hours under certain weather conditions, there can be no HWRF data released in days. One hour interval between each job are suggested. The script for each job check if there is the new data need to be processed.  
Use [corntab](https://www.digitalocean.com/community/tutorials/how-to-use-cron-to-automate-tasks-ubuntu-1804) command to create/edit cron jobs. 
Sample cron setup, it assumes the miniconda is installed under /home/tester/miniconda3, use the absolute path to the python installation in the cron setup. Keep at least 1 hour interval between any two jobs. Sample crontab entries:  
```
0 0,8,16 * * * cd /home/tester/MoMProduction && /home/tester/miniconda3/envs/mom/bin/python MoM_run.py -j GFMS > /dev/null 2>&1
0 1,7,13,19 * * * cd /home/tester/MoMProduction && /home/tester/miniconda3/envs/mom/bin/python MoM_run.py -j HWRF  >/dev/null 2>&1
00 2,9,14,20 * * * cd /home/tester/MoMProduction && /home/tester/miniconda3/envs/mom/bin/python MoM_run.py -j DFO >/dev/null 2>&1
00 3,10,15,21 * * * cd /home/tester/MoMProduction && /home/tester/miniconda3/envs/mom/bin/python MoM_run.py -j VIIRS  >/dev/null 2>&1
```
**Notes:** Please reference [crontab_list.txt](https://github.com/Global-Flood-Assessment/MoMProduction/blob/dev/crontab_list.txt) for the latest cron setup. 
## 5. Storage requirements 
The minimum required free disk space for data processing is 20G. 

Daily processing jobs generate less than 3.0Gb data, includes both the downloaded data and products.  

Processing folder holds the downloaded data and intermediate outputs, all the contents under processing can be deleted periodically to save the disk space. The processed data is usually archived daily as a zip, such as gfms_20211202.zip in its corresponding folder. For DFO/VIIRS data, setting storage save flag to False in production.cfg deletes the downloaded data immediately after the processing, it saves a little more than 2.0Gb (DFO: 2Gb, VIIRS: around 200Mb). 
``` 
production.cfg:

[storage]
dfo_save: False 
viirs_save: False 
```
### 5.1 Free up disk space
If the disk space is low, use the following steps to free up disk space:
* Remove the zip files in sub-folders under Processing, the zip files contain the downloaded data that already been processed, it is safe to delete them periodically.
* If more space needed, under Products, all the tiffs images in _image subfolder can be removed, they are only for the archive purpose.  
* A good practice is to delete the older *.zip/*.tiff first, and keep at least the recent data up to two weeks. 

Disk space can be monitored with the optional Monitor Module. 
## 6. Folder structures 
Folder structures is defined in production.cfg, the default one is listed. Modify [general],[processing_dir], [products_dir] to change the locations. 
```
MoM
├── Processing
│   ├── dfo
│   ├── gfms
│   ├── glofas
│   ├── hwrf
│   ├── logs
│   └── viirs
└── Products
    ├── DFO
    │   ├── DFO_image
    │   ├── DFO_MoM
    │   └── DFO_summary
    ├── Final_Alert
    ├── GFMS
    │   ├── GFMS_image
    │   ├── GFMS_MoM
    │   └── GFMS_summary
    ├── GLOFAS
    ├── HWRF
    │   ├── HWRF_image
    │   ├── HWRF_MoM
    │   └── HWRF_summary
    └── VIIRS
        ├── VIIRS_image
        ├── VIIRS_MoM
        └── VIIRS_summary
```

## 7. Processing modules & data

```
MoM_run.py 
GFMS_tool.py
GFMS_MoM.py
HWRF_tool.py
HWRF_MoM.py
DFO_tool.py
DFO_MoM.py
VIIRS_tool.py
VIIRS_MoM.py

settings.py
utilities.py
initialize.py
```
The data required is in data folder:
```
data
├── Admin0_1_union_centroid.csv
├── Attributes.csv
├── DFO_Weightage.csv
├── GFMS_Weightage.csv
├── HWRF_Weightage.csv
├── Resilience_Index.csv
└── VIIRS_Weightage.csv
```
