"""
Create pdf files from Tableau dashboards. Requires tabcmd.exe,
available for free download here: https://www.tableau.com/support/releases/server
Created by James D. Triveri (BSD 3-Clause)
"""
import sys
import os
import os.path
import subprocess
import configparser
import multiprocessing
import itertools
import PyPDF2
import datetime
import shutil
import cx_Oracle
import sqlalchemy
import numpy as np
import pandas as pd
import PyPDF2



### NOTE: Use forward slashes ("/") to delimit file paths, not backslashes ("\").
SERVER   = "tableau.cna.com"
USER     = "cac9159"
PASSWORD = "FJ7865bn"
TABCMD   = "C:/Program Files/Tableau/Tableau Server/10.0/extras/Command Line Utility/tabcmd.exe"
VIEW_URL = "/views/LargeLossExpectationsDashboard_JDT/LargeLossSummary"
PDF_DIR  = "U:/TableauPDFOutput/"
PROXY    = "proxy.cna.com:8080"
TIMEOUT  = 120
NBRPROCS = 4

### Oracle authentication details.
DATABASE  = "PMLTP"
SCHEMA    = "MRI"
PASSWORD  = "xtq73vmxx"
TABLENAME = "LL_MODEL_GROUPS"

# Parameters to vary at each iteration.
THRESHOLDS = ["1","250000","500000","1000000", "3000000", "5000000", "10000000"]
GROUPINGS  = ["SBU", "SEGMENT"] #"PROGRAM_CODE",



def collate_pdfs(pdflist, pdfname):
    """
    Collate documents referenced in pdflist.
    :param pdflist: List of PDF filepaths.
    :param pdfname: Name of collated PDF file.
    :return: None
    """
    merger = PyPDF2.PdfFileMerger()
    try:
        for i in pdflist:
            merger.append(PyPDF2.PdfFileReader(open(i, 'rb')))
        merger.write(pdfname)
    finally:
        merger.close()


class PdfProcess(multiprocessing.Process):
    """Threaded PDF generation utility."""
    def __init__(self, lock, stream, queue1, queue2, **kwargs):
        # super().__init__(tri, **kwargs)
        # threading.Thread.__init__(self)
        super().__init__(lock=lock, stream=stream, queue1=queue1, queue2=queue2, **kwargs)
        self.queue1  = queue1
        self.queue2  = queue2
        self.stream  = stream
        self.lock    = lock
        self.tabcmd  = kwargs.get("tabcmd", "C:/Program Files/Tableau/Tableau Server/10.0/extras/Command Line Utility/tabcmd.exe")
        self.passwd  = kwargs.get("password", "FJ7865bn")
        self.proxy   = kwargs.get("proxy", "proxy.cna.com:8080")
        self.timeout = kwargs.get("timeout", 120)


    def run(self):
        """Submit URL specification and download PDF file."""
        while True:
            # Retrieve spec from queue1, then write PDF paths to queue2.
            grp, thr, url, pdf = self.queue1.get()

            if grp is None:
                # Poison pill method to shutdown running Process.
                self.queue1.task_done()
                break

            try:
                procargs = [
                    self.tabcmd, "get", url, "--filename", pdf, "--password",
                    self.passwd, "--proxy", self.proxy, "--timeout",
                    str(self.timeout), "--no-certcheck"
                    ]

                iterproc = subprocess.Popen(procargs, shell=False)
                iterproc.communicate()

                with self.lock:
                    if iterproc.returncode==0:
                        self.stream.write(
                            "Success => {} @ {}: `{}` created.".format(grp, thr, pdf)
                            )
                    self.queue2.put(pdf)
                    else:
                        self.stream.write(
                            "Failure => {} @ {}: `{}` not created".format(grp, thr, pdf)
                                )
            finally:
                self.queue1.task_done()









if __name__ == "__main__":

    configs = configparser.ConfigParser()

    logger_path = PDF_DIR + "tab2pdfLog.txt"
    flog = open(logger_path, "w")
    lock = multiprocessing.Lock()

    now = datetime.datetime.today().strftime("%Y-%m-%d @ %I:%M:%S%p")
    flog.write(" + [{}] Retrieving LLE groups.".format(now))

    # Initialize Oracle connection.
    connstr = "oracle://{}:{}@{}".format(SCHEMA,PASSWORD,DATABASE)
    conn    = sqlalchemy.create_engine(connstr)
    SQL     = "SELECT * FROM {}".format(TABLENAME)
    mgDF    = pd.read_sql_query(SQL, con=conn)
    mgDF.columns = mgDF.columns.str.upper()
    grpsdict = {i:mgDF[i].unique().tolist() for i in GROUPINGS}


    # Set working directory to PDF_DIR if exists.
    now      = datetime.datetime.today().strftime("%Y%m%d")
    _pdf_dir = PDF_DIR.rstrip("/") if PDF_DIR.endswith("/") else PDF_DIR
    output_dir = _pdf_dir + "/Tableau_Exhibits_" + now + "/"
    if os.path.isdir(output_dir): shutil.rmtree()
    os.mkdir(output_dir)

    # Produce PDF for each combination of THRESHOLDS and GROUPS.
    # Create Tableau server session - Login only once.
    try:
        loginargs = [
            TABCMD, "login", "--server", SERVER, "--username", USER,
            "--password", PASSWORD, "--proxy", PROXY, "--timeout", str(TIMEOUT),
            "--no-certcheck"
            ]

        loginproc = subprocess.Popen(loginargs, shell=False)
        loginproc.communicate()
        now = datetime.datetime.today().strftime("%Y-%m-%d @ %I:%M:%S%p")
        if loginproc.returncode==0:
            print(" + [{}] Successfully authenticated to {}".format(now, SERVER))
        else:
            print(" + [{}] Unable to authenticate to {}".format(now, SERVER))
            sys.exit(-1)

        # Iterate over each group.
        for k in grpsdict:

            itergrps_init = grpsdict[k]

            for j in THRESHOLDS:

                queue1 = multiprocessing.JoinableQueue() # Task queue
                queue2 = multiprocessing.Queue()         # PDFs queue

                itergrps = [i.replace(" ", "%20") for i in itergrps_init]
                iterthsh = [j for i in range(len(itergrps))]
                iterurls = [
                    VIEW_URL + "?Select%20Business=" + i + "&THRESHOLD=" + j + ".pdf"
                        for i in itergrps]
                iterpdfs = [
                    output_dir + i.replace(" ", "_") + "_" + j + ".pdf"
                        for i in itergrps]

                all_specs = list(zip(itergrps, iterthsh, iterurls, iterpdfs))
                for spec in all_specs: queue1.put(spec)

                # Add a poison pill for each consumer.
                for p in range(NUMPROCS):
                    queue1.put((None, None, None, None))

                # Initialize NBRPROCS parallel processes.
                kwdargs = {
                    "tabcmd":TABCMD,"password":PASSWORD,"proxy":PROXY,"timeout":TIMEOUT
                    }

                parprocs = [
                    PdfProcess(lock=lock,stream=flog,queue1=queue1,queue2=queue2,**kwdargs)
                        for i in NUMPROCS
                    ]

                consumers = [Consumer(tasks, results) for i in range(num_consumers)]
                for w in consumers: w.start()


                self.queue1  = queue1
                self.queue2  = queue2
                self.stream  = stream
                self.lock    = lock
                #self.tabcmd  = kwargs.get("tabcmd", "C:/Program Files/Tableau/Tableau Server/10.0/extras/Command Line Utility/tabcmd.exe")
                #self.passwd  = kwargs.get("password", "FJ7865bn")
                #self.proxy   = kwargs.get("proxy", "proxy.cna.com:8080")
                self.timeout = kwargs.get("timeout", 120)

                SERVER   = "tableau.cna.com"
                USER     = "cac9159"
                PASSWORD = "FJ7865bn"
                TABCMD   = "C:/Program Files/Tableau/Tableau Server/10.0/extras/Command Line Utility/tabcmd.exe"
                VIEW_URL = "/views/LargeLossExpectationsDashboard_JDT/LargeLossSummary"
                PDF_DIR  = "U:/TableauPDFOutput/"
                PROXY    = "proxy.cna.com:8080"
                TIMEOUT  = 120
                NUMPROCS = 4





                #grp, thresh, url, pdf


                # for i in params:
                #     grp, thresh = i[0], i[1]
                #     # Encode url.
                #     itergrp = grp.replace(" ", "%20")
                #     iterurl = VIEW_URL + "?Select%20Business=" + itergrp + "&THRESHOLD=" + thresh + ".pdf"
                #     iterpdf = output_dir + grp.replace(" ", "_") + "_" + thresh + ".pdf"
                #
                #     # Compile command line arguments for pdf retrieval.
                #     procargs = [
                #         TABCMD, "get", iterurl, "--filename", iterpdf, "--password", PASSWORD,
                #         "--proxy", PROXY, "--timeout", str(TIMEOUT), "--no-certcheck"
                #         ]

                    # # Dispatch procargs.
                    # try:
                    #     iterproc = subprocess.Popen(procargs, shell=False)
                    #     iterproc.communicate()
                    #     now = datetime.datetime.today().strftime("%Y-%m-%d @ %I:%M:%S%p")
                    #     if iterproc.returncode==0:
                    #         print(" + [{}] `{}` successfully created.".format(now, iterpdf))
                    #         pdflist.append(iterpdf)
                    # except:
                    #     print(" + [{}] An error occurred exporting {}".format(now, iterpdf))
                    #     continue

            # Collate group/threshold pdfs into single document.
            now = datetime.datetime.today().strftime("%Y-%m-%d @ %I:%M:%S%p")
            print(" + [{}] Now collating {}.".format(now, threshpdf))
            threshpdf = output_dir + str(k) + "_" + str(j) + ".pdf"
            collate_pdfs(pdflist=pdflist, pdfname=threshpdf)

    finally:
        logoutargs = [TABCMD, "logout"]
        logoutproc = subprocess.Popen(logoutargs, shell=False)
        logoutproc.communicate()
        now = datetime.datetime.today().strftime("%Y-%m-%d @ %H:%M:%S")
        if logoutproc.returncode==0:
            print(" + [{}] Server session successfully terminated.".format(now))


    # Merge PDFs and save to PDF_DIR.
    # if "--collate" in sys.argv[1:]:
    #
    #     import PyPDF2
    #
    #     merger = PyPDF2.PdfFileMerger()
    #
    #     for i in all_pdfs:
    #         merger.append(PyPDF2.PdfFileReader(open(i, 'rb')))
    #
    #     all_pdfs_name = output_dir + "All_Groups.pdf"
    #     merger.write(iter_rpname)
    #     merger.close()
