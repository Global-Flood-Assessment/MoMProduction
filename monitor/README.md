# Monitor Service
Monitor service check the latest outputs in Products to check the system operation status, if a data set is not produced on time, it will flag the operation status as **warning**.  

## Sample status report
```
Operation Status: Normal
Report time: 20220404, 17:29:52
Data Processing
GLOFAS : 20220404 : threspoints_2022040400.csv
GFMS : 20220404 : Flood_byStor_2022040421.csv
HWRF : 20220404 : hwrf.2022040400rainfall.csv
DFO : 20220403 : DFO_20220403.csv
VIIRS : 20220402 : VIIRS_Flood_20220402.csv
MoM Output
GFMS : 20220404 : Attributes_Clean_20220404.csv
HWRF : 20220403 : Attributes_clean_2022040312HWRF+20220402DFO+20220402VIIRSUpdated.csv
DFO : 20220403 : Attributes_Clean_2022040318MOM+DFOUpdated.csv
VIIRS : 20220402 : Attributes_clean_2022040218MOM+DFO+VIIRSUpdated.csv
FINAL : 20220403 : Final_Attributes_2022040306HWRF+MOM+DFO+VIIRSUpdated_PDC.csv
```
**Notes:** in html email, the warning item is marked by red

## Send email
The current code use [sendgrid](https://sendgrid.com/) free account, install [sendgrid python client](https://github.com/sendgrid/sendgrid-python/) under the virtual environment running MoM code. 
```
pip install sendgrid
```
## Modify configuration:
monitor_config.cfg
```
[EMAIL]
from_email = someone@example.com
to_emails = someone@example.com,someoneelse@example.com
SENDGRID_API_KEY = xxxx
```
Email can send to one or multiple addresses (separated by ",").  
**Notes:** sendMail function can be updated to use other send mail services, such as [smtplib](https://docs.python.org/3.9/library/smtplib.html)

## Test
run **python monitor.py**, an email shall be received in several minutes with the status report.

## Add to Crobtab
If the server is on UTC (+0000) time, this setup will send a report at 8:30 and 4:30 EDT.
```
30 12,20 * * * cd /home/tester/MoMProduction/monitor && /home/tester/miniconda3/envs/mom/bin/python monitor.py  >/dev/null 2>&1
```
