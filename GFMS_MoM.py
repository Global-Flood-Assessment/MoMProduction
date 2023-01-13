import csv
import os

import numpy as np
import pandas as pd
import scipy.stats

import settings
from utilities import read_data


def mofunc_gfms(row):
    if row["Severity"] > 0.8 or row["Hazard_Score"] > 80:
        return "Warning"
    elif 0.6 < row["Severity"] < 0.80 or 60 < row["Hazard_Score"] < 80:
        return "Watch"
    elif 0.35 < row["Severity"] < 0.6 or 35 < row["Hazard_Score"] < 60:
        return "Advisory"
    elif 0 < row["Severity"] < 0.35 or 0 < row["Hazard_Score"] < 35:
        return "Information"


def flood_severity(GFMS_Table, GloFas_Table, adate):

    # outputs file
    Final_Attributes_csv = os.path.join(
        settings.GFMS_MOM_DIR, "Final_Attributes_{}.csv".format(adate)
    )
    Attributes_Clean_csv = os.path.join(
        settings.GFMS_MOM_DIR, "Attributes_Clean_{}.csv".format(adate)
    )

    # already processed
    if os.path.exists(Final_Attributes_csv) and os.path.exists(Attributes_Clean_csv):
        # print('already processed: ',adate)
        return

    # GFMS_Weightage.csv
    weightage = read_data(os.path.join(settings.BASE_DIR, "data", "GFMS_Weightage.csv"))
    add_field_GloFas = [
        "Alert_Score",
        "PeakArrivalScore",
        "TwoYScore",
        "FiveYScore",
        "TwtyYScore",
        "Sum_Score",
    ]
    add_field_GFMS = [
        "GFMS_area_score",
        "GFMS_perc_area_score",
        "MeanD_Score",
        "MaxD_Score",
        "Duration_Score",
        "Sum_Score",
    ]
    #  Reading GFMS Table with latest data having duration score
    with open(GFMS_Table, "r", encoding="UTF-8") as GFMS_file:
        GFMS_reader = csv.reader(GFMS_file)
        # shall put in GFMS_PROC_DIR
        GFMS_w_score_csv = "GFMS_w_score_{}.csv".format(adate)
        GFMS_w_score_csv = os.path.join(settings.GFMS_PROC_DIR, GFMS_w_score_csv)
        csvfile = open(GFMS_w_score_csv, "w", newline="\n", encoding="utf-8")
        GFMS_w_score = csv.writer(csvfile)
        row_count = 1
        # csv_writer = csv.writer(write_obj)
        for row in GFMS_reader:
            if row_count == 1:
                for x in add_field_GFMS:
                    row.append(x)
                row_count = row_count + 1
            else:
                if float(row[1]) / float(weightage.GFMS_Area_wt) > float(
                    weightage.GFMS_Area_max_pt
                ):
                    GFMS_area_score = str(float(weightage.GFMS_Area_max_pt))
                else:
                    GFMS_area_score = str(
                        float(weightage.GFMS_Area_Min_pt)
                        * float(row[1])
                        / float(weightage.GFMS_Area_wt)
                    )
                if float(row[2]) / float(weightage.GFMS_percArea_wt) > float(
                    weightage.GFMS_percArea_Maxpt
                ):
                    GFMS_perc_area_score = str(float(weightage.GFMS_percArea_Maxpt))
                else:
                    GFMS_perc_area_score = str(
                        float(weightage.GFMS_percArea_Minpt)
                        * float(row[2])
                        / float(weightage.GFMS_percArea_wt)
                    )
                if float(row[3]) / float(weightage.GFMS_Meandepth_wt) > float(
                    weightage.GFMS_Meandepth_Maxpt
                ):
                    MeanD_Score = str(float(weightage.GFMS_Meandepth_Maxpt))
                else:
                    MeanD_Score = str(
                        float(weightage.GFMS_Meandepth_Minpt)
                        * float(row[3])
                        / float(weightage.GFMS_Meandepth_wt)
                    )
                if float(row[4]) / float(weightage.GFMS_Maxdepth_wt) > float(
                    weightage.GFMS_Maxdepth_Maxpt
                ):
                    MaxD_Score = str(float(weightage.GFMS_Maxdepth_Maxpt))
                else:
                    MaxD_Score = str(
                        float(weightage.GFMS_Maxdepth_Minpt)
                        * float(row[4])
                        / float(weightage.GFMS_Maxdepth_wt)
                    )
                if float(row[5]) / float(weightage.GFMS_Duration_wt) > float(
                    weightage.GFMS_Duration_Maxpt
                ):
                    Duration_Score = str(float(weightage.GFMS_Duration_Maxpt))
                else:
                    Duration_Score = str(
                        float(weightage.GFMS_Duration_Minpt)
                        * float(row[5])
                        / float(weightage.GFMS_Duration_wt)
                    )
                Sum_Score = str(
                    float(GFMS_area_score)
                    + float(GFMS_perc_area_score)
                    + float(MeanD_Score)
                    + float(MaxD_Score)
                    + float(Duration_Score)
                )
                score_field = [
                    GFMS_area_score,
                    GFMS_perc_area_score,
                    MeanD_Score,
                    MaxD_Score,
                    Duration_Score,
                    Sum_Score,
                ]
                for x in score_field:
                    row.append(x)
            GFMS_w_score.writerow(row)
    csvfile.close()
    # GFMS Done

    # Reading GloFas Table

    with open(GloFas_Table, "r", encoding="UTF-8") as GloFas_file:
        GloFas_reader = csv.reader(GloFas_file)
        GloFas_w_score_csv = os.path.join(
            settings.GFMS_PROC_DIR, "GloFas_w_score_{}.csv".format(adate)
        )
        GloFas_Error_csv = os.path.join(
            settings.GFMS_PROC_DIR, "GloFas_Error_{}.csv".format(adate)
        )
        csvfile = open(GloFas_w_score_csv, "w", newline="\n", encoding="utf-8")
        txtfile = open(GloFas_Error_csv, "w", newline="\n")
        GloFas_w_score = csv.writer(csvfile)
        errorfile = csv.writer(txtfile)
        error_flag = False
        row_count = 1
        for row in GloFas_reader:
            if row_count == 1:
                for x in add_field_GloFas:
                    row.append(x)
                write = [
                    row[14],
                    row[12],
                    row[13],
                    row[9],
                    row[10],
                    row[11],
                    row[15],
                    row[16],
                    row[17],
                    row[18],
                    row[19],
                    row[20],
                ]
                GloFas_w_score.writerow(write)
                errorfile.writerow([row[0], row[1], row[14], "Error"])
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
                if (
                    int(row[9]) == 0
                    and int(row[10]) == 0
                    and int(row[11]) == 0
                    and int(row[12]) == 0
                ):
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
                    float(Alert_Score)
                    + float(PeakArrival_Score)
                    + float(TwoYScore)
                    + float(FiveYScore)
                    + float(TwtyYScore)
                )
                score_field = [
                    Alert_Score,
                    PeakArrival_Score,
                    TwoYScore,
                    FiveYScore,
                    TwtyYScore,
                    Sum_Score,
                ]
                for x in score_field:
                    row.append(x)
                write = [
                    row[14],
                    row[12],
                    row[13],
                    row[9],
                    row[10],
                    row[11],
                    row[15],
                    row[16],
                    row[17],
                    row[18],
                    row[19],
                    row[20],
                ]
                GloFas_w_score.writerow(write)
    csvfile.close()
    txtfile.close()
    if not error_flag:
        os.remove(GloFas_Error_csv)

    # Taking average of Hazard score from glofas for same pfaf_id
    GloFas = read_data(GloFas_w_score_csv)
    GloFas.sort_values(by="pfaf_id", ascending=True, inplace=True)
    GloFas_w_score_sort_csv = os.path.join(
        settings.GFMS_PROC_DIR, "GloFas_w_score_sort_{}.csv".format(adate)
    )
    GloFas.set_index("pfaf_id").to_csv(GloFas_w_score_sort_csv, encoding="utf-8")

    with open(GloFas_w_score_sort_csv, "r") as GloFas_file:
        GloFas_reader = csv.reader(GloFas_file)
        GloFas_w_Avgscore_csv = os.path.join(
            settings.GFMS_PROC_DIR, "GloFas_w_Avgscore_{}.csv".format(adate)
        )
        csvfile = open(GloFas_w_Avgscore_csv, "w", newline="\n", encoding="utf-8")
        GloFas_w_score = csv.writer(csvfile)
        Haz_Score = 0
        pfaf_id = -1
        similarity = 0
        i = 1
        To_be_written = "False"
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
                    To_be_written = "True"
                else:
                    last_row[11] = str(Haz_Score / similarity)
                    GloFas_w_score.writerow(last_row)
                    last_row = row
                    pfaf_id = row[0]
                    Haz_Score = float(row[11])
                    similarity = 1
                    To_be_written = "True"
    if To_be_written == "True":
        last_row[11] = str(Haz_Score / similarity)
        GloFas_w_score.writerow(last_row)
    csvfile.close()
    # Glofas Done
    os.remove(GloFas_w_score_sort_csv)

    # Read Watershed attribute and join the GloFas and GFMs Score and calculate severity
    GFMS = read_data(GFMS_w_score_csv)
    GloFas = read_data(GloFas_w_Avgscore_csv)
    Attributes = read_data(os.path.join(settings.BASE_DIR, "data", "Attributes.csv"))
    join = pd.merge(
        GloFas.set_index("pfaf_id"),
        GFMS.set_index("pfaf_id"),
        on="pfaf_id",
        how="outer",
    )
    PDC_resilience = read_data(
        os.path.join(settings.BASE_DIR, "data", "Resilience_Index.csv")
    )
    join1 = pd.merge(
        Attributes,
        PDC_resilience[["ISO", "Resilience_Index", " NormalizedLackofResilience "]],
        on="ISO",
        how="inner",
    )
    Final_Attributes = pd.merge(
        join1.set_index("pfaf_id"), join, on="pfaf_id", how="outer"
    )
    Final_Attributes[["Sum_Score_x", "Sum_Score_y"]] = Final_Attributes[
        ["Sum_Score_x", "Sum_Score_y"]
    ].fillna(value=0)
    Final_Attributes["Sum_Score_x"][(Final_Attributes["Sum_Score_y"] == 0)] = (
        Final_Attributes["Sum_Score_x"] * 2
    )
    Final_Attributes["Sum_Score_y"][(Final_Attributes["Sum_Score_x"] == 0)] = (
        Final_Attributes["Sum_Score_y"] * 2
    )
    Final_Attributes = Final_Attributes.assign(
        Hazard_Score=lambda x: Final_Attributes["Sum_Score_x"]
        + Final_Attributes["Sum_Score_y"]
    )
    # Final_Attributes = Final_Attributes.assign(
    # Scaled_Riverine_Risk=lambda x: Final_Attributes['rfr_score'] * 20 * Final_Attributes[' NormalizedLackofResilience '])
    Final_Attributes = Final_Attributes[Final_Attributes.Hazard_Score != 0]
    Final_Attributes.drop(
        Final_Attributes.index[
            (Final_Attributes["rfr_score"] == 0) & (Final_Attributes["cfr_score"] == 0)
        ],
        inplace=True,
    )
    Final_Attributes = Final_Attributes.assign(
        Scaled_Riverine_Risk=lambda x: Final_Attributes["rfr_score"] * 20
    )
    Final_Attributes = Final_Attributes.assign(
        Scaled_Coastal_Risk=lambda x: Final_Attributes["cfr_score"] * 20
    )
    Final_Attributes = Final_Attributes[Final_Attributes.Hazard_Score != 0]
    # Final_Attributes = Final_Attributes.assign(
    # Severity=lambda x: scipy.stats.norm(np.log(100 - Final_Attributes['Scaled_Riverine_Risk']), 1).cdf(
    # np.log(Final_Attributes['Hazard_Score'])))
    Final_Attributes = Final_Attributes.assign(
        Severity=lambda x: scipy.stats.norm(
            np.log(
                100
                - Final_Attributes[["Scaled_Riverine_Risk", "Scaled_Coastal_Risk"]].max(
                    axis=1
                )
            ),
            1,
        ).cdf(np.log(Final_Attributes["Hazard_Score"]))
    )

    Final_Attributes["Alert"] = Final_Attributes.apply(mofunc_gfms, axis=1)
    # Final_Attributes['Mod_Alert'] = Final_Attributes.apply(func, axis=1)
    # Final_Attributes.to_csv('Final_Attributes', encoding='utf-8-sig')
    Final_Attributes.to_csv(Final_Attributes_csv, encoding="utf-8-sig")

    Attributes_Clean = pd.merge(
        join1.set_index("pfaf_id"),
        Final_Attributes[["Alert"]],
        on="pfaf_id",
        how="right",
    )
    # Attributes_Clean = pd.merge(join1.set_index('pfaf_id'), Final_Attributes[['Alert', 'Mod_Alert']], on='pfaf_id', how='right')
    # Attributes_Clean.to_csv('Attributes_Clean.csv', encoding='utf-8-sig')
    Attributes_Clean.to_csv(Attributes_Clean_csv, encoding="utf-8-sig")

    os.remove(GloFas_w_score_csv)
    os.remove(GloFas_w_Avgscore_csv)
    os.remove(GFMS_w_score_csv)


def main():
    # flood_severity("../data/testdata/gfms_fix/Flood_byStor_2020051600.csv","../data/testdata/glofas/threspoints_2020051600.csv","20200516")
    # flood_severity("../data/testdata/gfms_fix/Flood_byStor_2020051700.csv","../data/testdata/glofas/threspoints_2020051700.csv","20200517")
    # flood_severity("../data/testdata/gfms_fix/Flood_byStor_2020051800.csv","../data/testdata/glofas/threspoints_2020051800.csv","20200518")
    # flood_severity("../data/testdata/gfms_fix/Flood_byStor_2020051900.csv","../data/testdata/glofas/threspoints_2020051900.csv","20200519")
    # flood_severity("../data/testdata/gfms_fix/Flood_byStor_2020052000.csv","../data/testdata/glofas/threspoints_2020052000.csv","20200520")
    # flood_severity("../data/testdata/gfms_fix/Flood_byStor_2020052100.csv","../data/testdata/glofas/threspoints_2020052100.csv","20200521")
    # flood_severity("../data/testdata/gfms_fix/Flood_byStor_2020052200.csv","../data/testdata/glofas/threspoints_2020052200.csv","20200522")
    # flood_severity("../data/testdata/gfms_fix/Flood_byStor_2020052300.csv","../data/testdata/glofas/threspoints_2020052300.csv","20200523")
    # flood_severity("../data/testdata/gfms_fix/Flood_byStor_2020052400.csv","../data/testdata/glofas/threspoints_2020052400.csv","20200524")
    # flood_severity("../data/testdata/gfms_fix/Flood_byStor_2020052500.csv","../data/testdata/glofas/threspoints_2020052500.csv","20200525")
    # flood_severity("../data/testdata/gfms_fix/Flood_byStor_2020052600.csv","../data/testdata/glofas/threspoints_2020052600.csv","20200526")
    # flood_severity("../data/testdata/gfms_fix/Flood_byStor_2020052700.csv","../data/testdata/glofas/threspoints_2020052700.csv","20200527")
    # flood_severity("../data/testdata/gfms_fix/Flood_byStor_2020052800.csv","../data/testdata/glofas/threspoints_2020052800.csv","20200528")
    # flood_severity("../data/testdata/gfms_fix/Flood_byStor_2020052900.csv","../data/testdata/glofas/threspoints_2020052900.csv","20200529")
    # for i in range(1,16):
    #     d_st = str(i).zfill(2)
    #     gfms = "../data/testdata/gfms_fix/Flood_byStor_202006%s00.csv" % d_st
    #     glofas = "../data/testdata/glofas/threspoints_202006%s00.csv" % d_st
    #     adate = "202006" + d_st
    #     print(d_st)
    #     flood_severity(gfms,glofas,adate)
    flood_severity(
        "../data/testdata/gfms_fix/Flood_byStor_2020061700.csv",
        "../data/testdata/glofas/threspoints_2020061700.csv",
        "20200617",
        "../data/testdata/flood",
    )


if __name__ == "__main__":
    main()
