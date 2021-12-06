"""
    HWRF_MoM.py
        -- HWRF and MoM integration
"""

import csv
import pandas as pd
import os
import scipy.stats
import numpy as np
from datetime import date,timedelta,datetime
import glob
import logging

import settings
from utilities import read_data

def mofunc_hwrf(row):
    if row['Severity'] > 0.8 or row['Hazard_Score'] > 80:
        return 'Warning'
    elif 0.6 < row['Severity'] < 0.80 or 60 < row['Hazard_Score'] < 80:
        return 'Watch'
    elif 0.35 < row['Severity'] < 0.6 or 35 < row['Hazard_Score'] < 60:
        return 'Advisory'
    elif 0 < row['Severity'] < 0.35 or 0 < row['Hazard_Score'] < 35:
        return 'Information'

def update_HWRF_MoM(adate):
    """ HWRF MoM for a date: YYYYMMDDHH"""

    gfms_sum = os.path.join(settings.GFMS_SUM_DIR, "Flood_byStor_{}.csv".format(adate))
    glofas_sum = os.path.join(settings.GLOFAS_DIR,"threspoints_{}00.csv".format(adate[:-2]))
    hwrf_sum = os.path.join(settings.HWRF_SUM_DIR,"hwrf.{}rainfall.csv".format(adate))

    # first check if file exists
    if not os.path.exists(gfms_sum):
        print("not found: ",gfms_sum)
        return
    if not os.path.exists(glofas_sum):
        print("not found: ", glofas_sum)
        return
    
    #hwrf_sum may not have
    Final_Attributes_csv = os.path.join(settings.HWRF_MOM_DIR,'Final_Attributes_{}HWRFUpdated.csv'.format(adate))
    Attributes_Clean_csv = os.path.join(settings.HWRF_MOM_DIR,'Attributes_Clean_{}HWRFUpdated.csv'.format(adate))

    #already processed
    if (os.path.exists(Final_Attributes_csv) and os.path.exists(Attributes_Clean_csv)):
        print('already processed: ',adate)
        return 
    
    weightage = read_data(os.path.join(settings.BASE_DATA_DIR,'GFMS_Weightage.csv'))
    HWRF_weightage = read_data(os.path.join(settings.BASE_DATA_DIR,'HWRF_Weightage.csv'))
    add_field_GloFas = ['Alert_Score', 'PeakArrivalScore', 'TwoYScore', 'FiveYScore', 'TwtyYScore', 'Sum_Score']
    add_field_GFMS = ['GFMS_area_score', 'GFMS_perc_area_score', 'MeanD_Score', 'MaxD_Score', 'Duration_Score', 'Sum_Score']
    add_field_HWRF=['HWRF_area_score', 'HWRF_percarea_score', 'MeanRain_Score', 'MaxRain_Score', 'HWRFTot_Score']

    #Read GFMS Processing data and calculte score
    with open(gfms_sum, 'r', encoding='UTF-8') as GFMS_file:
        GFMS_reader = csv.reader(GFMS_file)
        GFMS_w_score_csv = "GFMS_w_score_{}.csv".format(adate)
        GFMS_w_score_csv = os.path.join(settings.HWRF_PROC_DIR,GFMS_w_score_csv)
        csvfile = open(GFMS_w_score_csv, 'w', newline='\n', encoding='utf-8')
        GFMS_w_score = csv.writer(csvfile)
        row_count = 1
        # csv_writer = csv.writer(write_obj)
        for row in GFMS_reader:
            if row_count == 1:
                for x in add_field_GFMS:
                    row.append(x)
                row_count = row_count + 1
            else:
                if float(row[1]) / float(weightage.GFMS_Area_wt) > float(weightage.GFMS_Area_max_pt):
                    GFMS_area_score = str(float(weightage.GFMS_Area_max_pt))
                else:
                    GFMS_area_score = str(float(weightage.GFMS_Area_Min_pt) * float(row[1]) / float(weightage.GFMS_Area_wt))
                if float(row[2]) / float(weightage.GFMS_percArea_wt) > float(weightage.GFMS_percArea_Maxpt):
                    GFMS_perc_area_score = str(float(weightage.GFMS_percArea_Maxpt))
                else:
                    GFMS_perc_area_score = str(float(weightage.GFMS_percArea_Minpt) * float(row[2]) / float(weightage.GFMS_percArea_wt))
                if float(row[3]) / float(weightage.GFMS_Meandepth_wt) > float(weightage.GFMS_Meandepth_Maxpt):
                    MeanD_Score = str(float(weightage.GFMS_Meandepth_Maxpt))
                else:
                    MeanD_Score = str(float(weightage.GFMS_Meandepth_Minpt)*float(row[3]) / float(weightage.GFMS_Meandepth_wt))
                if float(row[4]) / float(weightage.GFMS_Maxdepth_wt) > float(weightage.GFMS_Maxdepth_Maxpt):
                    MaxD_Score = str(float(weightage.GFMS_Maxdepth_Maxpt))
                else:
                    MaxD_Score = str(float(weightage.GFMS_Maxdepth_Minpt) * float(row[4]) / float(weightage.GFMS_Maxdepth_wt))
                if float(row[5]) / float(weightage.GFMS_Duration_wt) > float(weightage.GFMS_Duration_Maxpt):
                    Duration_Score = str(float(weightage.GFMS_Duration_Maxpt))
                else:
                    Duration_Score = str(float(weightage.GFMS_Duration_Minpt) * float(row[5]) / float(weightage.GFMS_Duration_wt))
                Sum_Score = str(
                    float(GFMS_area_score) + float(GFMS_perc_area_score) + float(MeanD_Score) + float(MaxD_Score) + float(
                        Duration_Score))
                score_field = [GFMS_area_score, GFMS_perc_area_score, MeanD_Score, MaxD_Score, Duration_Score, Sum_Score]
                for x in score_field:
                    row.append(x)
            GFMS_w_score.writerow(row)
    csvfile.close()

    ##Read GloFas data and Calculate score
    with open(glofas_sum, 'r', encoding='UTF-8') as GloFas_file:
        GloFas_reader = csv.reader(GloFas_file)
        GloFas_w_score_csv = "GloFas_w_score_{}.csv".format(adate)
        GloFas_w_score_csv = os.path.join(settings.HWRF_PROC_DIR,GloFas_w_score_csv)
        GloFas_Error_csv = "GloFas_Error_{}.csv".format(adate)
        GloFas_Error_csv = os.path.join(settings.HWRF_PROC_DIR,GloFas_Error_csv)
        csvfile = open(GloFas_w_score_csv, 'w', newline='\n', encoding='utf-8')
        txtfile = open(GloFas_Error_csv, 'w', newline='\n')
        GloFas_w_score = csv.writer(csvfile)
        errorfile = csv.writer(txtfile)
        row_count = 1
        error_flag = False
        for row in GloFas_reader:
            if row_count == 1:
                for x in add_field_GloFas:
                    row.append(x)
                write = [row[14], row[12], row[13], row[9], row[10], row[11], row[15], row[16], row[17], row[18], row[19],
                        row[20]]
                GloFas_w_score.writerow(write)
                errorfile.writerow([row[0], row[1], row[14], 'Error'])
                row_count = row_count + 1
            elif float(row[12]) > 3 or float(row[12]) < 0:
                error = "Alert less than 0 or greater than 3 is encountered"
                errorfile.writerow([row[0], row[1], row[14], error])
                error_flag = True
            elif float(row[9]) > 100:
                error = "2 yr EPS greater than 100 is encountered"
                errorfile.writerow([row[0], row[1], row[14], error])
                error_flag = True
            elif float(row[10]) > 100:
                error = "5 yr EPS greater than 100 is encountered"
                errorfile.writerow([row[0], row[1], row[14], error])
                error_flag = True
            elif float(row[11]) > 100:
                error = "20 yr EPS greater than 100 is encountered"
                errorfile.writerow([row[0], row[1], row[14], error])
                error_flag = True
            elif float(row[13]) > 30:
                error = "Peak arrival days greater than 30 is encountered"
                errorfile.writerow([row[0], row[1], row[14], error])
                error_flag = True
            else:
                Alert_Score = str(round(float(row[12]) * float(weightage.Alert_score)))
                TwoYScore = str(float(row[9]) / float(weightage.EPS_Twoyear_wt))
                FiveYScore = str(float(row[10]) / float(weightage.EPS_Fiveyear_wt))
                TwtyYScore = str(float(row[11]) / float(weightage.EPS_Twtyyear_wt))
                if int(row[9]) == 0 and int(row[10]) == 0 and int(row[11]) == 0 and int(row[12]) == 0:
                    PeakArrival_Score = str(0)
                elif int(row[13]) == 10 or int(row[13]) > 10:
                    PeakArrival_Score = str(1)
                elif int(row[13]) == 9:
                    PeakArrival_Score = str(2)
                elif int(row[13]) == 8:
                    PeakArrival_Score = str(3)
                elif int(row[13]) == 7:
                    PeakArrival_Score = str(4)
                elif int(row[13]) == 6:
                    PeakArrival_Score = str(5)
                elif int(row[13]) == 5:
                    PeakArrival_Score = str(6)
                elif int(row[13]) == 4:
                    PeakArrival_Score = str(7)
                elif int(row[13]) == 3:
                    PeakArrival_Score = str(8)
                elif int(row[13]) == 2:
                    PeakArrival_Score = str(9)
                elif int(row[13]) == 1:
                    PeakArrival_Score = str(10)
                Sum_Score = str(
                    float(Alert_Score) + float(PeakArrival_Score) + float(TwoYScore) + float(FiveYScore) + float(
                        TwtyYScore))
                score_field = [Alert_Score, PeakArrival_Score, TwoYScore, FiveYScore, TwtyYScore, Sum_Score]
                for x in score_field:
                    row.append(x)
                write = [row[14], row[12], row[13], row[9], row[10], row[11], row[15], row[16], row[17], row[18], row[19],
                    row[20]]
                GloFas_w_score.writerow(write)
    
    csvfile.close()
    txtfile.close()
    if not error_flag:
        os.remove(GloFas_Error_csv)
    GloFas = read_data(GloFas_w_score_csv)
    GloFas.sort_values(by='pfaf_id', ascending=True, inplace=True)
    GloFas_w_score_sort_csv = "GloFas_w_score_sort_{}.csv".format(adate)
    GloFas_w_score_sort_csv = os.path.join(settings.HWRF_PROC_DIR, GloFas_w_score_sort_csv)
    GloFas.set_index('pfaf_id').to_csv(GloFas_w_score_sort_csv, encoding='utf-8')

    with open(GloFas_w_score_sort_csv, 'r') as GloFas_file:
        GloFas_reader = csv.reader(GloFas_file)
        GloFas_w_Avgscore_csv = "GloFas_w_Avgscore_{}.csv".format(adate)
        GloFas_w_Avgscore_csv = os.path.join(settings.HWRF_PROC_DIR, GloFas_w_Avgscore_csv)
        csvfile = open(GloFas_w_Avgscore_csv, 'w', newline='\n', encoding='utf-8')
        GloFas_w_score = csv.writer(csvfile)
        Haz_Score = 0
        pfaf_id = -1
        similarity = 0
        i = 1
        To_be_written = 'False'
        write = []
        for row in GloFas_reader:
            if i == 1:
                i = i + 1
                GloFas_w_score.writerow(row)
            else:
                if pfaf_id == -1 or pfaf_id == row[0]:
                    pfaf_id = row[0]
                    Haz_Score = Haz_Score + float(row[11])
                    similarity = similarity + 1
                    last_row = row
                    To_be_written = 'True'
                else:
                    last_row[11] = str(Haz_Score / similarity)
                    GloFas_w_score.writerow(last_row)
                    last_row = row
                    pfaf_id = row[0]
                    Haz_Score = float(row[11])
                    similarity = 1
                    To_be_written = 'True'
    if To_be_written == 'True':
        last_row[11] = str(Haz_Score / similarity)
        GloFas_w_score.writerow(last_row)
    csvfile.close()
    # Glofas Done
    os.remove(GloFas_w_score_sort_csv)

    ## Read HWRF rainfall processed data and calculate separate hazard Score
    try:
        with open(hwrf_sum, 'r', encoding='UTF-8') as HWRF_file:
            HWRF_reader = csv.reader(HWRF_file)
            HWRF_w_score_csv = "HWRF_w_score_{}.csv".format(adate)
            HWRF_w_score_csv = os.path.join(settings.HWRF_PROC_DIR, HWRF_w_score_csv)
            csvfile = open(HWRF_w_score_csv, 'w', newline='\n', encoding='utf-8')
            HWRF_w_score = csv.writer(csvfile)
            row_count = 1
            # csv_writer = csv.writer(write_obj)
            for row in HWRF_reader:
                if row_count == 1:
                    for x in add_field_HWRF:
                        row.append(x)
                    HWRF_w_score.writerow(row)
                    row_count = row_count + 1
                elif row==[]:
                    continue
                else:
                    if float(row[1]) / float(HWRF_weightage.HWRF_Area_wt) > float(HWRF_weightage.HWRF_Area_max_pt):
                        HWRF_area_score = str(float(HWRF_weightage.HWRF_Area_max_pt))
                    else:
                        HWRF_area_score = str(float(HWRF_weightage.HWRF_Area_Min_pt) * float(row[1]) / float(HWRF_weightage.HWRF_Area_wt))
                    if float(row[2]) / float(HWRF_weightage.HWRF_percArea_wt) > float(HWRF_weightage.HWRF_percArea_Maxpt):
                        HWRF_percarea_score = str(float(HWRF_weightage.HWRF_percArea_Maxpt))
                    else:
                        HWRF_percarea_score = str(float(HWRF_weightage.HWRF_percArea_Minpt) * float(row[2]) / float(HWRF_weightage.HWRF_percArea_wt))
                    if float(row[3]) >= float(HWRF_weightage.HWRF_MeanRain_minwt):
                        if ((float(row[3])- float(HWRF_weightage.HWRF_MeanRain_minwt))/ float(HWRF_weightage.HWRF_MeanRain_increment))+float(HWRF_weightage.HWRF_MeanRain_Minpt) > float(HWRF_weightage.HWRF_MeanRain_Maxpt):
                            MeanRain_Score = str(float(HWRF_weightage.HWRF_MeanRain_Maxpt))
                        else:
                            MeanRain_Score = str(((float(row[3])- float(HWRF_weightage.HWRF_MeanRain_minwt))/ float(HWRF_weightage.HWRF_MeanRain_increment))+float(HWRF_weightage.HWRF_MeanRain_Minpt))
                    else:
                        MeanRain_Score='0'
                    if float(row[4]) >= float(HWRF_weightage.HWRF_MaxRain_minwt):                       
                        if ((float(row[4])- float(HWRF_weightage.HWRF_MaxRain_minwt))/ float(HWRF_weightage.HWRF_MaxRain_increment))+float(HWRF_weightage.HWRF_MaxRain_Minpt) > float(HWRF_weightage.HWRF_MaxRain_Maxpt):
                            MaxRain_Score = str(float(HWRF_weightage.HWRF_MaxRain_Maxpt))
                        else:
                            MaxRain_Score = str(((float(row[4])- float(HWRF_weightage.HWRF_MaxRain_minwt))/ float(HWRF_weightage.HWRF_MaxRain_increment))+float(HWRF_weightage.HWRF_MaxRain_Minpt))
                    else:
                        MaxRain_Score='0'
                    HWRFTot_Score = (float(HWRF_area_score)+float(HWRF_percarea_score)+ float(MeanRain_Score)+float(MaxRain_Score))*2.5 
                    results_list = [row[0], row[1], row[2], row[3], row[4],HWRF_area_score,HWRF_percarea_score,MeanRain_Score,MaxRain_Score, HWRFTot_Score]
                    HWRF_w_score.writerow(results_list)
    except:
        pass

    GFMS = read_data(GFMS_w_score_csv)
    GloFas = read_data(GloFas_w_Avgscore_csv)
    Attributes = read_data(os.path.join(settings.BASE_DATA_DIR,'Attributes.csv'))
    #HWRF=read_data('HWRF_w_score.csv')
    join = pd.merge(GloFas.set_index('pfaf_id'), GFMS.set_index('pfaf_id'), on='pfaf_id', how='outer')
    #join0=pd.merge(join, HWRF.set_index('pfaf_id'), on='pfaf_id', how='outer')
    PDC_resilience = read_data(os.path.join(settings.BASE_DATA_DIR,'Resilience_Index.csv'))
    join1 = pd.merge(Attributes, PDC_resilience[['ISO', 'Resilience_Index', ' NormalizedLackofResilience ']], on='ISO', how='inner')
    #Final_Attributes = pd.merge(join1.set_index('pfaf_id'), join0, on='pfaf_id', how='outer')
    Final_Attributes = pd.merge(join1.set_index('pfaf_id'), join, on='pfaf_id', how='outer')
    Final_Attributes[['Sum_Score_x', 'Sum_Score_y']] = Final_Attributes[['Sum_Score_x', 'Sum_Score_y']].fillna(value=0)
    Final_Attributes['Sum_Score_x'][(Final_Attributes['Sum_Score_y'] == 0)] = Final_Attributes['Sum_Score_x']*2
    Final_Attributes['Sum_Score_y'][(Final_Attributes['Sum_Score_x'] == 0)] = Final_Attributes['Sum_Score_y']*2
    Final_Attributes = Final_Attributes.assign(
        MOM_Score=lambda x: Final_Attributes['Sum_Score_x'] + Final_Attributes['Sum_Score_y'])
    Final_Attributes['Hazard_Score']=Final_Attributes[['MOM_Score']]
    try:
        HWRF=read_data(HWRF_w_score_csv)
        Final_Attributes=pd.merge(Final_Attributes, HWRF.set_index('pfaf_id'), on='pfaf_id', how='outer')
        Final_Attributes['Flag']=np.where((Final_Attributes['Hazard_Score']<Final_Attributes['HWRFTot_Score']),1,'')
        Final_Attributes['Hazard_Score'] =Final_Attributes[['Hazard_Score', 'HWRFTot_Score']].max(axis=1)
    except:
        pass
    Final_Attributes = Final_Attributes[Final_Attributes.Hazard_Score != 0]
    Final_Attributes.drop(Final_Attributes.index[(Final_Attributes['rfr_score']==0) & (Final_Attributes['cfr_score']==0)], inplace=True)
    Final_Attributes = Final_Attributes.assign(
        Scaled_Riverine_Risk=lambda x: Final_Attributes['rfr_score'] * 20)
    Final_Attributes = Final_Attributes.assign(
        Scaled_Coastal_Risk=lambda x: Final_Attributes['cfr_score'] * 20)
    Final_Attributes = Final_Attributes.assign(
        Severity=lambda x: scipy.stats.norm(np.log(100 - Final_Attributes[['Scaled_Riverine_Risk', 'Scaled_Coastal_Risk']].max(axis=1)), 1).cdf(
            np.log(Final_Attributes['Hazard_Score'])))
    Final_Attributes['Alert'] = Final_Attributes.apply(mofunc_hwrf, axis=1)
    Final_Attributes.loc[Final_Attributes['Alert']=="Information",'Flag']=''
    Final_Attributes.loc[Final_Attributes['Alert']=="Advisory",'Flag']=''
    Final_Attributes.to_csv(Final_Attributes_csv, encoding='utf-8-sig')
    #Final_Attributes.to_csv('Final_Attributes_2021081606.csv', encoding='utf-8-sig')
    Attributes_Clean = pd.merge(join1.set_index('pfaf_id'), Final_Attributes[['Alert']], on='pfaf_id', how='right')
    Attributes_Clean.to_csv(Attributes_Clean_csv, encoding='utf-8-sig')
    logging.info('generated: ' + Final_Attributes_csv)
    
    # delete temp files
    os.remove(GloFas_w_score_csv)
    os.remove(GloFas_w_Avgscore_csv)
    os.remove(GFMS_w_score_csv)
    
    try:
        os.remove(HWRF_w_score_csv)
    except:
        pass

    return

def main():
    # run batch mode
    testdate = '2021120406'
    update_HWRF_MoM(testdate)

if __name__ == "__main__":
    main()   