# ModeofModels Production
The following guide is tested on Ubuntu 18.04 and 20.04 LTS.
## 1. Setup Python environment
### 1.1 Install Python
Python version: >= 3.8  
[Miniconda](https://docs.conda.io/en/latest/miniconda.html) is recommanded.  
Latest release: [Miniconda3 Linux 64-bit](https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh) 

**Note**: virtual evn is not recommanded in prodution.
### 1.2 Enable conda-forge channel
After miniconda installed, the commands enable conda-forge channel  
```
conda config --add channels conda-forge
conda config --set channel_priority strict
conda config --show channels
```
### 1.2 Install Packages

## 2. Clone MoMProduction repo:
```
git clone https://github.com/Global-Flood-Assessment/MoMProduction.git
```
## 3. Ininitlize the setup
Please copy [sample_production.cfg](https://github.com/Global-Flood-Assessment/MoMProduction/blob/main/sample_production.cfg) to **production.cfg**.  
Check production.cfg: 
- in general section, change WORKING_DIR (base directory for downloading and processing data) and PRODUCT_DIR (base directory for the data products) if necessary;
- in glofas section, fill in user/passwd for ftp site;  
- in dfo section, fill in token for download [more on Automating NRT Downloads](https://nrt4.modaps.eosdis.nasa.gov/archive/allData/61)  
```
[general]
WORKING_DIR: ~/MoM/Processing
OUTPUT_DIR: ~/MoM/Products

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
- check username/password, key in production.cfg
- unzip watershed.shp 

