"""
    monitor.py
        -- a simple monitor service

    notes on email:
        -- https://sendgrid.com/ free account
        -- https://github.com/sendgrid/sendgrid-python/
            pip install sendgrid
"""

import os,sys, glob
import re

current = os.path.dirname(os.path.realpath(__file__))

from datetime import date, datetime
parent = os.path.dirname(current)
sys.path.append(parent)

import settings
from utilities import from_today

monitor_data = ["GLOFAS","GFMS","HWRF","DFO","VIIRS"]
monitor_mom = ["GFMS","HWRF","DFO","VIIRS","FINAL"]

def findLatest(apath,atype):
    """return the latst file in folder"""
    check_path = os.path.join(apath,f"*.{atype}")
    all_files = glob.glob(check_path)
    latest_file = max(all_files, key=os.path.getctime)
    
    return os.path.basename(latest_file)

def extractDate(astr):
    """extract date from astr"""
    match_str = re.search(r'\d{8}', astr)
    adate = match_str.group()

    return adate

def writeStatus(statusdict, statusflag):
    """write status to html file"""

    htmlfile = os.path.join(settings.PRODUCT_DIR,"footer.html")
    htmlstr = ""
    if statusflag != "normal":
        htmlstr += '<h3>Operation Status: <span style="color:red">Warning</span></h3>'
    else:
        htmlstr += '<h3>Operation Status: <span style="color:green">Normal</span></h3>'

    htmlstr += "<h4>Report time: " + statusdict['checktime'] + "</h4>"

    htmlstr += "<h4>Data Processing</h4>"
    liststr = ""
    for item in monitor_data:
        textstr = item + " : " + statusdict[f'{item}_data_date'] + " : " + statusdict[f'{item}_data']
        if statusdict[f'{item}_data_status'] != 'normal':
            liststr += "<li>"+ f'<span style="color:red">{textstr}</span>'+ "</li>"
        else:
            liststr += "<li>"+ textstr + "</li>"

    htmlstr += f"<ul>{liststr}</ul>"
    htmlstr += "<h4>MoM Output</h4>"
    
    liststr = ""
    for item in monitor_mom:
        textstr = item + " : " + statusdict[f'{item}_MoM_date'] + " : " + statusdict[f'{item}_MoM']
        if statusdict[f'{item}_MoM_status'] != 'normal':
            liststr += "<li>"+ f'<span style="color:red">{textstr}</span>'+ "</li>"
        else:
            liststr += "<li>"+ textstr + "</li>"

    htmlstr += f"<ul>{liststr}</ul>"

    with open(htmlfile,"w") as f:
        f.write(htmlstr)
    
    return htmlstr

def sendEmail(statusreport,statusflag):
    """send email"""
    
    import configparser
    config = configparser.ConfigParser()
    config.read('monitor_config.cfg')
    from_email = config['EMAIL']['from_email']
    to_emails = config['EMAIL']['to_emails']
    sg_key = config['EMAIL']['SENDGRID_API_KEY']

    # send to multiple email address
    if "," in to_emails:
        to_emails = to_emails.split(",")

    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail

    subject = "Operation: " + statusflag

    message = Mail(
        from_email=from_email,
        to_emails = to_emails,
        subject = subject,
        html_content = statusreport )
    
    try:
        sg = SendGridAPIClient(sg_key)
        reponse = sg.send(message)
    except Exception as e:
        print(e.message)
    
    return

def checkService():
    """check service status"""
    # get the date
    status = {}
    today = date.today()
    d1 = today.strftime("%Y%m%d")
    status['checktime'] = datetime.utcnow().strftime("%Y%m%d, %H:%M:%S")
    operation_status = "normal"

    for item in monitor_data:
        the_folder = eval("settings." + item + "_SUM_DIR")
        latest = findLatest(the_folder,"csv")
        status[f"{item}_data"] = latest
        adate = extractDate(latest)
        status[f"{item}_data_date"] = adate
        fdays = from_today(adate)
        status[f"{item}_data_status"] = "normal"

        if item in ["GLOFAS","GFMS","HWRF"] and fdays < -1:
            status[f"{item}_data_status"] = "warning"
            operation_status = "warning"
        if item in ["DFO","VIIRS"] and fdays < -2:
            status[f"{item}_data_status"] = "warning"
            operation_status = "warning"

    for item in monitor_mom:
        the_folder = eval("settings." + item + "_MOM_DIR")
        latest = findLatest(the_folder,"csv")
        status[f"{item}_MoM"] = latest
        adate = extractDate(latest)
        status[f"{item}_MoM_date"] = adate
        fdays = from_today(adate)
        status[f"{item}_MoM_status"] = "normal"
        
        if item in ["GFMS","HWRF","FINAL"] and fdays < -1:
            status[f"{item}_MoM_status"] = "warning"
            operation_status = "warning"
        if item in ["DFO","VIIRS"] and fdays < -2:
            status[f"{item}_MoM_status"] = "warning"
            operation_status = "warning"

    #print(status)
    msg = writeStatus(status, operation_status)
    # sedn email with 
    sendEmail(msg,operation_status)

def main():
    checkService()

if __name__ == "__main__":
    main()