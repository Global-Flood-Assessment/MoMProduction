"""
monitor.py
    -- a simple monitor service

notes on email:
    -- https://sendgrid.com/ free account
    -- https://github.com/sendgrid/sendgrid-python/
        pip install sendgrid
"""

import configparser
import glob
import os
import re
import shutil
import sys
from datetime import date, datetime

# add path
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import settings
from utilities import from_today, hwrf_today

monitor_data = ["GLOFAS", "GFMS", "HWRF", "DFO", "VIIRS"]
monitor_mom = ["GFMS", "HWRF", "DFO", "VIIRS", "FINAL"]

config = configparser.ConfigParser()
config.read("monitor_config.cfg")


def findLatest(apath, atype):
    """return the latest file in folder"""
    check_path = os.path.join(apath, f"*.{atype}")
    all_files = glob.glob(check_path)
    # latest_file = max(all_files, key=os.path.getctime)
    # date str is in YYYYMMDDHH format, string sort is enought
    latest_file = max(all_files)

    return os.path.basename(latest_file)


def extractDate(astr):
    """extract date from astr"""
    match_str = re.search(r"\d{8}", astr)
    adate = match_str.group()

    return adate


def writeStatus(statusdict, statusflag, diskflag=""):
    """write status to html file"""

    htmlfile = os.path.join(settings.PRODUCT_DIR, "footer.html")
    htmlstr = ""
    if statusflag != "normal":
        htmlstr += '<h3>Operation Status: <span style="color:red">Warning</span></h3>'
    else:
        htmlstr += '<h3>Operation Status: <span style="color:green">Normal</span></h3>'

    htmlstr += "<h4>Report time: " + statusdict["checktime"] + "</h4>"

    htmlstr += "<h4>Data Processing</h4>"
    liststr = ""
    for item in monitor_data:
        textstr = (
            item
            + " : "
            + statusdict[f"{item}_data_date"]
            + " : "
            + statusdict[f"{item}_data"]
        )
        if statusdict[f"{item}_data_status"] != "normal":
            liststr += "<li>" + f'<span style="color:red">{textstr}</span>' + "</li>"
            if item == "HWRF":
                liststr += (
                    "HWRF data release at "
                    + statusdict["checktime"].split(",")[0]
                    + " : "
                    + str(hwrf_today())
                )
        else:
            liststr += "<li>" + textstr + "</li>"

    htmlstr += f"<ul>{liststr}</ul>"
    htmlstr += "<h4>MoM Outputs</h4>"

    liststr = ""
    for item in monitor_mom:
        textstr = (
            item
            + " : "
            + statusdict[f"{item}_MoM_date"]
            + " : "
            + statusdict[f"{item}_MoM"]
        )
        if statusdict[f"{item}_MoM_status"] != "normal":
            liststr += "<li>" + f'<span style="color:red">{textstr}</span>' + "</li>"
        else:
            liststr += "<li>" + textstr + "</li>"

    htmlstr += f"<ul>{liststr}</ul>"

    # add check disk section
    if statusdict["checkDisk"]:
        if diskflag != "normal":
            htmlstr += '<h4>Disk Status: <span style="color:red">Warning</span></h3>'
        else:
            htmlstr += '<h3>Disk Status: <span style="color:green">Normal</span></h3>'

        liststr = ""
        for item in statusdict["diskstatus"]:
            # "disk","freespace","status"
            textstr = (
                item["disk"]
                + ": freespace "
                + "{:.2f}".format(item["freespace"])
                + " Gb"
            )
            if item["status"] != "normal":
                liststr += (
                    "<li>" + f'<span style="color:red">{textstr}</span>' + "</li>"
                )
            else:
                liststr += "<li>" + textstr + "</li>"
        htmlstr += f"<ul>{liststr}</ul>"

    with open(htmlfile, "w") as f:
        f.write(htmlstr)

    return htmlstr


def sendEmail(statusreport, reportsubject):
    """send email"""

    from_email = config["EMAIL"]["from_email"]
    to_emails = config["EMAIL"]["to_emails"]
    sg_key = config["EMAIL"]["SENDGRID_API_KEY"]

    # send to multiple email address
    if "," in to_emails:
        to_emails = to_emails.split(",")

    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail

    message = Mail(
        from_email=from_email,
        to_emails=to_emails,
        subject=reportsubject,
        html_content=statusreport,
    )

    try:
        sg = SendGridAPIClient(sg_key)
        reponse = sg.send(message)
    except Exception as e:
        print(e.message)

    return


def sendEmailSMTP(statusreport, reportsubject):
    """send email with SMTP server"""

    from_email = config["SMTP"]["from_email"]
    to_emails = config["SMTP"]["to_emails"]

    # send to multiple email address
    if "," in to_emails:
        to_emails = to_emails.split(",")

    from email.message import EmailMessage

    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = to_emails
    msg["Subject"] = reportsubject
    msg.set_content("status report")
    msg.add_alternative(statusreport, subtype="html")

    import smtplib

    smtpServer = config["SMTP"]["server"]
    smtpPort = config["SMTP"]["port"]
    server = smtplib.SMTP(host=smtpServer, port=smtpPort)
    if config.has_option("SMTP", "login"):
        smtpLogin = config["SMTP"]["login"]
        server.login("apikey", smtpLogin)
    server.set_debuglevel(1)
    server.send_message(msg)
    server.quit()


def sendGmail(statusreport, reportsubject):
    """send email with SMTP server"""

    from_email = config["GMAIL"]["from_email"]
    to_emails = config["GMAIL"]["to_emails"]

    # send to multiple email address
    if "," in to_emails:
        to_emails = to_emails.split(",")

    from email.message import EmailMessage

    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = to_emails
    msg["Subject"] = reportsubject
    msg.set_content("status report")
    msg.add_alternative(statusreport, subtype="html")

    import smtplib
    import ssl

    smtpServer = config["GMAIL"]["server"]
    smtpPort = config["GMAIL"]["port"]
    smtpPassword = config["GMAIL"]["password"]
    # Create a secure SSL context
    context = ssl.create_default_context()

    try:
        with smtplib.SMTP_SSL(smtpServer, smtpPort, context=context) as smtp_server:
            smtp_server.login(from_email, smtpPassword)
            smtp_server.sendmail(from_email, to_emails, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")


def checkService():
    """check service status"""
    # get the date
    status = {}
    today = date.today()
    d1 = today.strftime("%Y%m%d")
    status["checktime"] = datetime.utcnow().strftime("%Y%m%d, %H:%M:%S")
    operation_status = "normal"

    for item in monitor_data:
        the_folder = eval("settings." + item + "_SUM_DIR")
        latest = findLatest(the_folder, "csv")
        status[f"{item}_data"] = latest
        adate = extractDate(latest)
        status[f"{item}_data_date"] = adate
        fdays = from_today(adate)
        status[f"{item}_data_status"] = "normal"

        if item in ["GLOFAS", "GFMS"] and fdays < -1:
            status[f"{item}_data_status"] = "warning"
            operation_status = "warning"
        if item in ["DFO", "VIIRS"] and fdays < -2:
            status[f"{item}_data_status"] = "warning"
            operation_status = "warning"
        # hwrf will not show warning
        if item in ["HWRF"] and fdays < -1:
            status[f"{item}_data_status"] = "warning"

    for item in monitor_mom:
        the_folder = eval("settings." + item + "_MOM_DIR")
        latest = findLatest(the_folder, "csv")
        status[f"{item}_MoM"] = latest
        adate = extractDate(latest)
        status[f"{item}_MoM_date"] = adate
        fdays = from_today(adate)
        status[f"{item}_MoM_status"] = "normal"

        if item in ["GFMS", "HWRF", "FINAL"] and fdays < -1:
            status[f"{item}_MoM_status"] = "warning"
            operation_status = "warning"
        if item in ["DFO", "VIIRS"] and fdays < -2:
            status[f"{item}_MoM_status"] = "warning"
            operation_status = "warning"

    # check if it has the disk section
    status["checkDisk"] = False
    disk_status = ""
    if config.has_section("DISK"):
        [disk_status, status["diskstatus"]] = checkDisk()
        status["checkDisk"] = True

    # print(status)
    msg = writeStatus(status, operation_status, disk_status)
    # email subject
    email_subject = "Operation: " + operation_status
    if status["checkDisk"]:
        email_subject += " | Disk: " + disk_status

    # send email
    if config.has_section("EMAIL"):
        sendEmail(msg, email_subject)

    if config.has_section("SMTP"):
        sendEmailSMTP(msg, email_subject)

    if config.has_section("GMAIL"):
        sendGmail(msg, email_subject)


def checkDisk():
    """check the disk space"""

    diskstatusL = []
    disk_status_flag = "normal"
    for k, v in config.items("DISK"):
        disk_label = k
        disk_mount, disk_threshold = v.split(",")
        disk_threshold = float(disk_threshold)
        disk_usage = shutil.disk_usage(disk_mount)
        # convert to GB
        freespace = disk_usage.free / (10**9)
        if freespace < disk_threshold:
            d_status = "warning"
            disk_status_flag = "warning"
        else:
            d_status = "normal"
        diskstatusL.append(
            {"disk": disk_label, "freespace": freespace, "status": d_status}
        )

    return [disk_status_flag, diskstatusL]


def main():
    checkService()


if __name__ == "__main__":
    main()
