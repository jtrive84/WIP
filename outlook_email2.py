import win32com.client
import psutil
import os
from subprocess import Popen, PIPE








# Drafting and sending email notification to senders. You can add other senders' email in the list
# import win32com.client
#
# s = win32com.client.Dispatch("Mapi.Session")
# o = win32com.client.Dispatch("Outlook.Application")
# s.Logon("Outlook2003")
#
# Msg = o.CreateItem(0)
# Msg.To = "recipient@domain.com"
#
# Msg.CC = "more email addresses here"
# Msg.BCC = "more email addresses here"
#
# Msg.Subject = "The subject of you mail"
# Msg.Body = "The main body text of you mail"
#
# attachment1 = "Path to attachment no. 1"
# attachment2 = "Path to attachment no. 2"
# Msg.Attachments.Add(attachment1)
# Msg.Attachments.Add(attachment2)
#
# Msg.Send()


def is_running(proc_name:str) -> bool:
    """
    Check whether the process identified as `proc_name` is running.
    """
    with Popen("tasklist /NH /FO TABLE", shell=False, stdout=PIPE) as proc:
        rprocs = proc.stdout.read().decode("utf-8")
        plist  = rprocs.split("\r\n")
    return(any(i.lower().startswith(proc_name.lower()) for i in plist))



# def send2(recipients):
#     import win32com.client as win32
#     outlook = win32.Dispatch("Outlook.Application")
#     mail = outlook.CreateItem(0)
#     mail.Subject = "Test Email"
#     mail.HtmlBody = "Message Body"
#
#     if hasattr(recipients, 'strip'):
#         recipients = [recipients]
#
#     [mail.Recipients.Add(i) for i in recipients]
#
#
#
#     # mail.To = "James.Triveri@cna.com"
#     mail.Attachments.Add("U:/sample.txt")
#     mail.send



OUTLOOK_EXE = "C:\\Program Files\\Microsoft Office\\Office15\\OUTLOOK.EXE"

def send_email(path=OUTLOOK_EXE,subject="",message="",recipients=None,
               cc=None,bcc=None,attachments=None):
    """
    Send email using Outlook. Sender is assumed to be the logged-in user.
    Outlook needs to be running. If Outlook is not running, an attempt
    is made to launch Outlook.

    # mail.To  = "James.Triveri@cna.com"
    # mail.CC  = "more email addresses here"
    # mail.BCC = "more email addresses here"
    # Msg.Body = "The main body text of you mail"
    """
    # Check if outlook is an active process.
    if not is_running(os.path.basename(path)):

        # Launch Outlook executable.
        cmdspec = 'start "" /B /MIN ' + '"' + path + '"'
        subprocess.run(cmdspec, shell=True, capture_output=False)

        # Wait until `OUTLOOK.EXE` registers in tasklist.
        while True:
            if not is_running(os.path.basename(path)):
                time.sleep(.25)
            else:
                break

    # Send message via Outlook and logged in user.
    outlook       = win32com.client.Dispatch("Outlook.Application")
    mail          = outlook.CreateItem(0)
    mail.Subject  = subject
    mail.HtmlBody = message

    if recipients is not None:
        if hasattr(recipients, "strip"):
            recipients = [recipients]
        [mail.Recipients.Add(i) for i in recipients]

    if attachments is not None:
        if hasattr(attachments, "strip"):
            attachments = [attachments]
        [mail.Attachments.Add(i) for i in attachments]

    mail.send

    return(None)



send_email(
    path=OUTLOOK_EXE,
    subject="Test Email Subject",
    message="Test email message",
    recipients="James.Triveri@cna.com"
    )
