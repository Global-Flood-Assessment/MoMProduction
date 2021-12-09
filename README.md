# ModeofModels Production
The following guide is tested on Ubuntu 18.04 and 20.04 LTS.  
The current testing VM is a m1.small instance on [Jetstream clound](https://portal.xsede.org/jetstream) with 2 vcous, 4GB memory, 20GB storage with an extra 100GB volume attached.   
## 1. Setup Python environment
### 1.1 Install Python
Python version tested: 3.8, 3.9    
[Miniconda](https://docs.conda.io/en/latest/miniconda.html) is recommanded.  
Latest release: [Miniconda3 Linux 64-bit](https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh) 
### 1.2 Enable conda-forge channel
After miniconda installed, the commands enable conda-forge channel  
```
conda config --add channels conda-forge
conda config --set channel_priority strict
conda config --show channels
```
### 1.2 Install Python Packages
```
conda install --file packagelist.txt 
```
If an environment is prefered:
```
conda create --name myenv --file packagelist.txt
```
**Note**: virtual environment is not recommanded in prodution.  
### 1.3 Other software requirements
Check if zip, wget, gdal are installed.  
Install the packages if not available:
```
sudo apt install gdal_bin 
```

## 2. Clone MoMProduction repo:
```
git clone https://github.com/Global-Flood-Assessment/MoMProduction.git
```
## 3. Ininitlize the setup
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
Ininitlize the production setup: 
```
python initialize.py
```
It performs the following taks:   
- create the folder structures defined in production.cfg
- check username/password, token in production.cfg
- unzip watershed.shp 

## 4. Test run
All the processing jobs can be tested in the following orders. It may take several hours to finish, it produces data products from the latest several days.
```
python MoM_run.py -j GFMS
python MoM_run.py -j HWRF
python MoM_run.py -j DFO
python MoM_run.py -j VIIRS
```
The outputs to the console are very minimal, the progress can be checked through the log file under processing/logs folder. The log is generated each month, e.g 2021_11.log, 2021_12.log.    
## 4. Setup cron jobs
Each datasets are released in difference schedules, GloFAS, DFO, VIIRS are released once a day; GFMS are the predication data in 3-hour interval and available in advance, amd are processed along with GloFAS data. HWRF is updated every 6 six hours under certain weather conditions, there can be no HWRF data released in days. One hour interval between each job are suggested. The script for each job check if there is the new data need to be processed.  
Use [corntab](https://www.digitalocean.com/community/tutorials/how-to-use-cron-to-automate-tasks-ubuntu-1804) command to create/edit cron jobs. 
Sample cron setup, it assumes the miniconda is installed under /home/tester/miniconda3, use the abosulte path to your python instatllation in the crom setup.   
```

```
## 5. Storages requirements 
The minimum required free diskspace for data processing is 20G. 

Daily processing jobs generate less than 3.0Gb data, includes both the downloaded data and products.  

Processing folder holds the downloaded data and intermediate outputs, all the contents under processing can be deleted periodically to save the disk space. The processed data is usually archived daily as a zip, such as gfms_20211202.zip in its corresponding folder. For DFO/VIIRS data, setting storage save flag to False in production.cfg deletes the downloaded data immediately after the processing, it saves a little more than 2.0Gb (DFO: 2Gb, VIIRS: around 200Mb). 
``` 
production.cfg:

[storage]
dfo_save: False 
viirs_save: False 
```
## 5. Folder structures 
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

## 6. Processing modules & data

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
