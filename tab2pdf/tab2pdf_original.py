"""
Create pdf files from Tableau dashboards. Requires tabcmd.exe,
available for free download here: https://www.tableau.com/support/releases/server
Created by James D. Triveri (BSD 3-Clause)
"""
import sys
import os
import os.path
import configparser
import subprocess
import itertools
import datetime
import re
import shutil



### NOTE: Use forward slashes ("/") to delimit file paths, not backslashes ("\").
SERVER   = "tableau.cna.com"
USER     = "cac9159"
PASSWORD = "FJ7865bn"
TABCMD   = "C:/Program Files/Tableau/Tableau Server/10.0/extras/Command Line Utility/tabcmd.exe"
VIEW_URL = "/views/LargeLossExpectationsDashboard_JDT/LargeLossSummary"
PDF_DIR  = "U:/Repos"
PROXY    = "proxy.cna.com:8080"
TIMEOUT  = 120

# Parameters to vary at each iteration.
THRESHOLDS = ["1","250000","500000","1000000"]#, "3000000", "5000000", "10000000"]
GROUPS     = ["Small Business"]
params     = itertools.product(GROUPS, THRESHOLDS)
all_pdfs   = []



if __name__ == "__main__":

    # Read in settings from settings.cfg in same folder as
    config  = configparser.ConfigParser()
    cfgdir  = os.path.dirname(__file__)
    cfgpath = cfgdir + os.path.sep + "settings.cfg"
    config.read(cfgpath)

    SERVER   = config["SETTINGS"]["SERVER"]
    PROXY    = config["SETTINGS"]["PROXY"]
    USER     = config["SETTINGS"]["USER"]
    PASSWORD = config["SETTINGS"]["PASSWORD"]
    TABCMD   = config["SETTINGS"]["TABCMD"]
    VIEW_URL = config["SETTINGS"]["VIEW_URL"]
    PDF_DIR  = config["SETTINGS"]["PDF_DIR"]
    INPUTS   = config["SETTINGS"]["INPUTS"]
    TIMEOUT  = config["SETTINGS"]["TIMEOUT"]

    # Set working directory to PDF_DIR if exists.
    now  = datetime.datetime.today().strftime("%Y%m%d")
    pdf_dir_ = PDF_DIR.rstrip("/").rstrip("\\") if \
        any(PDF_DIR.endswith(i) for i in ("\\","/")) else PDF_DIR

    output_dir = pdf_dir_ + os.path.sep + "Tableau_Exhibits_" + now + os.path.sep
    if os.path.isdir(output_dir): shutil.rmtree()
    os.mkdir(output_dir, mode=770)
    all_specs = []

    # Produce PDF for each combination of values present in `INPUTS`.
    # Headers in file represent Tableau exhibit elements to be filtered
    # (these are case sensitive). The number of PDFs generated will
    # exactly match the number of records present in `INPUTS`.
    with open(INPUTS, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            keysinit, valsinit = list(row.keys()), list(row.values())
            iterkeys = [re.sub("\\s{1,}","%20",i) for i in keysinit]
            itervals = [re.sub("\\s{1,}","%20",i) for i in valsinit]
            iterspec = "&".join(i + "=" + j for i,j in zip(iterkeys,itervals))
            all_specs.append(iterspec)

    # Login to Tableau server, tableau.cna.com.
    try:
        loginargs = [
            TABCMD, "login",
            "--server", SERVER,
            "--username", USER,
            "--password", PASSWORD,
            "--proxy", PROXY,
            "--timeout", str(TIMEOUT),
            "--no-certcheck"
            ]

        loginproc = subprocess.Popen(loginargs, shell=False)
        loginproc.communicate()
        now = datetime.datetime.today().strftime("%Y-%m-%d @ %H:%M:%S")
        if loginproc.returncode==0:
            print(" + [{}] Successfully authenticated to {}".format(now, SERVER))
        else:
            print(" + [{}] Unable to authenticate to {}".format(now, SERVER))
            sys.exit(1)

        # Iterate over all_specs appending each set of specified parameters
        # to the specified workbook/view basename, given by `VIEW_URL`.
        for i in all_specs:







        for i in params:
            grp, thresh = i[0], i[1]
            # Encode url.
            itergrp = grp.replace(" ", "%20")
            iterurl = VIEW_URL + "?Select%20Business=" + itergrp + "&THRESHOLD=" + thresh + ".pdf"
            iterpdf = output_dir + grp.replace(" ", "_") + "_" + thresh + ".pdf"

            # Compile command line arguments for pdf retrieval.
            procargs = [
                TABCMD, "get", iterurl,
                "--filename", iterpdf,
                "--password", PASSWORD,
                "--proxy", PROXY,
                "--timeout", str(TIMEOUT),
                "--no-certcheck"
                ]

            # Dispatch procargs.
            try:
                iterproc = subprocess.Popen(procargs, shell=False)
                iterproc.communicate()
                now = datetime.datetime.today().strftime("%Y-%m-%d @ %H:%M:%S")
                if iterproc.returncode==0:
                    print(" + [{}] `{}` successfully created.".format(now, iterpdf))
                    all_pdfs.append(iterpdf)
            except:
                print(" + [{}] An error occurred exporting {}".format(now, iterpdf))
                continue

    finally:
        logoutargs = [TABCMD, "logout"]
        logoutproc = subprocess.Popen(logoutargs, shell=False)
        logoutproc.communicate()
        now = datetime.datetime.today().strftime("%Y-%m-%d @ %H:%M:%S")
        if logoutproc.returncode==0:
            print(" + [{}] Server session successfully terminated.".format(now))


    # Merge PDFs and save to PDF_DIR.
    if "--collate" in sys.argv[1:]:

        import PyPDF2

        merger = PyPDF2.PdfFileMerger()

        for i in all_pdfs:
            merger.append(PyPDF2.PdfFileReader(open(i, 'rb')))

        all_pdfs_name = output_dir + "All_Groups.pdf"
        merger.write(iter_rpname)
        merger.close()
