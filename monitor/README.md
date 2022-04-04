# Monitor Service
Monitor service check the latest outputs in Products to check the system operation status, if a data set is not produced on time, it will flag the oepration status as **warning**.  

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
