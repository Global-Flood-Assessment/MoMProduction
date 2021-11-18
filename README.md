# ModeofModels Production
The following guide is based on Ubuntu > 18.04
## 1. Setup Python environment
### 1.1 Install Python
Python version: >= 3.8  
[Miniconda](https://docs.conda.io/en/latest/miniconda.html) is recommanded.  
Latest release: [Miniconda3 Linux 64-bit](https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh) 

**Note**: virtual evn is not recommanded in prodution
### 1.2 Enable conda-forge channel
After miniconda installed, the commands enable conda-forge channel  
```
conda config --add channels conda-forge
conda config --set channel_priority strict
conda config --show channels
```
### 1.2 Install Packages

