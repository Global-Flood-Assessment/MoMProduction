"""
    issue55.py
        -- fix the performace issue on final_alert_pdc() in HWRF_MoM.py
"""
import csv
import glob
import logging
import os
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
import scipy.stats

import settings
from utilities import (
    findLatest,
    get_current_processing_datehour,
    get_latestitems,
    hour_diff,
    hwrf_today,
    read_data,
)


def find_pair_HWRFoutput(adate):
    """return pair of HWRF Mom output
    [MoM_adate, MoM_1daybefore]
    if not found: ["",""]
    """
    # first find the hwrf hour output
    hwrfh_list = glob.glob(os.path.join(settings.HWRF_MOM_DIR, "Final*.csv"))
    # Final_Attributes_2021102800HWRF+20211028DFO+20211027VIIRSUpdated.csv
    matching = [s for s in hwrfh_list if adate + "HWRF+" in s]
    if len(matching) < 1:
        return ["", ""]

    MoM_adate = matching[0]

    # generate string from the previous day
    # turn the datestr into a real date
    datestr = adate[:-2]
    hh = adate[-2:]
    da = datetime.strptime(datestr, "%Y%m%d")
    pda = da - timedelta(days=1)
    pdatestr = pda.strftime("%Y%m%d")
    # pdate
    pdate = pdatestr + hh
    matching = [s for s in hwrfh_list if pdate + "HWRF+" in s]
    # no previous date
    if len(matching) < 1:
        return [MoM_adate, ""]

    MoM_1daybefore = matching[0]

    return [MoM_adate, MoM_1daybefore]


def final_alert_pdc(adate):
    """generate final alert"""

    fAlert = "Final_Attributes_{}HWRF+MOM+DFO+VIIRSUpdated_PDC.csv".format(adate)
    fAlert = os.path.join(settings.FINAL_MOM, fAlert)
    # check if final alert is already generatated
    if os.path.exists(fAlert):
        return

    [aAlert, pAlert] = find_pair_HWRFoutput(adate)
    if aAlert == "" or pAlert == "":
        logging.warning(f"mathing HWRF output is not found: {adate}")
        return

    mapping = {"Information": 1, "Advisory": 2, "Watch": 3, "Warning": 4}
    # read data
    pa_df = read_data(pAlert)
    # for PA, the only two columns needed
    pa_df = pa_df[["pfaf_id", "Alert"]]
    ca_df = read_data(aAlert)
    pa_df = pa_df.replace({"Alert": mapping})
    ca_df = ca_df.replace({"Alert": mapping})

    # rename Alert in the previous day as Alert_0
    pa_df.rename(columns={"Alert": "Alert_0"}, inplace=True)
    # join two df by pfaf_id
    joined_df = ca_df.set_index("pfaf_id").join(pa_df.set_index("pfaf_id"))

    # check the value of Alert_0
    # expected value: [ 1.  2. nan  3.  4.]
    print(joined_df["Alert_0"].unique())
    # replace nan value as 5
    joined_df["Alert_0"] = joined_df["Alert_0"].fillna(5)
    # force it int
    joined_df = joined_df.astype({"Alert_0": int})
    # expected value Alert_0: [1 2 3 4 5]
    print(joined_df["Alert_0"].unique())
    # expected value Alert: [1 2 3 4]
    print(joined_df["Alert"].unique())

    # a new Status column based on Alert and Alert_0
    # Alert_0 = 5: "New"
    # Alert = Alert_0: "Continued"
    # Alert > Alert_0: "Upgraded"
    # Alert < Alert_0: "Downgraded"
    conditions = [
        (joined_df["Alert_0"] == 5),
        (joined_df["Alert"] == joined_df["Alert_0"]),
        (joined_df["Alert"] > joined_df["Alert_0"]),
        (joined_df["Alert"] < joined_df["Alert_0"]),
    ]
    actions = ["New", "Continued", "Upgraded", "Downgraded"]
    joined_df["Status"] = np.select(conditions, actions, default="Other")
    print(joined_df["Status"].unique())

    mapping = {1: "Information", 2: "Advisory", 3: "Watch", 4: "Warning"}
    joined_df = joined_df.replace({"Alert": mapping})

    # delete columns
    joined_df = joined_df.drop(
        [
            "Admin0",
            "Admin1",
            "ISO",
            "Resilience_Index",
            " NormalizedLackofResilience ",
            "Alert_0",
        ],
        axis=1,
    )

    # drop FID if it has
    if "FID" in joined_df.columns:
        print("drop FID column")
        joined_df = joined_df.drop(["FID"], axis=1)

    # load admin data
    Union_Attributes = pd.read_csv(
        os.path.join(settings.BASE_DATA_DIR, "Admin0_1_union_centroid.csv"),
        encoding="Windows-1252",
    )

    # reset index
    joined_df = joined_df.reset_index(level=0)
    PDC_Alert = pd.merge(Union_Attributes, joined_df, on="pfaf_id", how="inner")
    # print(PDC_Alert)
    PDC_Alert.drop(
        PDC_Alert.index[
            (PDC_Alert["DFOTotal_Score"] == "")
            & (PDC_Alert["MOM_Score"] == "")
            & (PDC_Alert["CentroidY"] > 50)
        ],
        inplace=True,
    )

    # drop FID if it has
    if "FID" in PDC_Alert.columns:
        print("drop FID column")
        PDC_Alert = PDC_Alert.drop(["FID"], axis=1)

    PDC_Alert.to_csv(fAlert, encoding="Windows-1252")
    logging.info("generated final alert:" + fAlert)

    return


def main():
    # run final_alert_pdc
    testdate = "2023011000"
    final_alert_pdc(testdate)
    testdate = "2023011100"
    final_alert_pdc(testdate)


if __name__ == "__main__":
    main()
