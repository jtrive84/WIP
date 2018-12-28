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
    all_specs, all_pdfs = [], []

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
            pdfname  = "_".join(re.sub("\\s{1,}","_",i) for i in valsinit).strip()
            iterpdf  = output_dir + pdfname + ".pdf"
            all_specs.append((iterspec,iterpdf))

    # Initialize single session - login to Tableau server.
    try:
        loginargs = [
            TABCMD, "login", "--server", SERVER,"--username", USER,
            "--password", PASSWORD, "--proxy", PROXY,"--timeout",
            str(TIMEOUT),"--no-certcheck"
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
        # to the specified workbook/view basename given by `VIEW_URL`.
        for i in all_specs:
            iterspec, iterpdf = i[0], i[1]
            iterurl = str(VIEW_URL) + "?" + spec + ".pdf"

            # Submit arguments for pdf generation. By specifying only
            # password and not password, server and username, the
            # established session will be used instead of creating
            # a new one.
            procargs = [
                TABCMD, "get", iterurl, "--filename", iterpdf,
                "--password", PASSWORD, "--proxy", PROXY,
                "--timeout", str(TIMEOUT), "--no-certcheck"
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


    # Merge PDFs and save to PDF_DIR if `--collate` present in argvs.
    if "--collate" in sys.argv[1:]:

        import PyPDF2

        merger = PyPDF2.PdfFileMerger()

        for i in all_pdfs:
            merger.append(PyPDF2.PdfFileReader(open(i, 'rb')))

        all_pdfs_name = output_dir + "All_Groups.pdf"
        merger.write(all_pdfs_name)
        merger.close()
