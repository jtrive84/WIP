# Import Modules
import os
from datetime import datetime
import numpy as np
import pandas as pd
import xlwings as xw
import sys

os.chdir("\\\\cna.com\\shared\\LTC_GGY_AXIS\\Stat and Tax Reserve Conversion\\2018 Build\\Python Emulator\\Calculator")



# Import scripts
import ALR_Stat
import Backend_Stat
import A_Load
import WoP
##import C_ALR_Stat


def MakeDir(Dir):
    r"""Check if current directory exists and if it does not create it"""
    if not(os.path.exists(Dir)):
        os.makedirs(Dir)

def GetDecrRates(CurData, Lapse_skew, OutputFolder):
    # ------------------------------------------
    # Assumptions Calculations
    # based on AXIS decrement method "5 - Convert to multiple decrement rates monthly - Constant force"
    # ------------------------------------------

    #get annual rates from A_Load (pol year 1 through 80)
    #convert to monthly
    qdTotal = np.repeat(CurData['FinalIncidence_Total'], 12) # total incidence used for decrement calculations
    qx = qdTotal * 0.0
    qw = np.repeat(CurData['Final_Lapse'], 12)
    qb = np.repeat(CurData['Final_Mortality'], 12)

    # qd = qd.reset_index(drop=True)
    # qx = qx.reset_index(drop=True)

    # Premium mode
    prem_mode = int(wb.sheets['Control'].range('prem_mode').value)
    if prem_mode == 3:
        Mode = 4
    elif prem_mode == 4:
        Mode = 12
    else:
        Mode = prem_mode
    PropYE = round(1 / float(Mode), 6)

    print "PropYE : " + str(PropYE)

    # apply skew lapse if applicable
    if not(Lapse_skew is None):
        qw = qw.reset_index(drop=True)
        print "yes skew lapse"
        Lapse_skew = np.array(Lapse_skew)
        qwprime = np.multiply(np.ones(len(qw)), qw)

        for i in range(0, (len(qw)/12) - 1):
            for mth in range(0, 12):
                qwprime[(i*12) + mth] = 1 - np.power((1 - qw[(i*12) + mth]),  float(Lapse_skew[mth]))
        pd.DataFrame.to_csv(pd.DataFrame(qwprime), OutputFolder + 'qw_times_skewlapse.csv')
    else:
        print "No skew lapse"
        months = np.mod(range(0, len(qw)), 12) + 1
        ind_YE_months = np.mod(months, (12/Mode)) == 0
        if Mode == 1:
            qwprime = qw * ind_YE_months
        else:
            qwprime = (1 - np.power((1 - qw), 1 / float(12))) * ind_YE_months

    qdTotalprime = 1 - np.power((1 - qdTotal), 1 / float(12))
    qbprime = 1 - np.power((1 - qb), 1 / float(12))
    qxprime = 1 - np.power((1 - qx), 1 / float(12))

    qdTotalFinal = np.multiply(qdTotalprime, 1 - ((qxprime + qbprime) / float(2)) + (np.multiply(qbprime, qxprime) / float(3)))
    qbFinal = np.multiply(qbprime, 1 - ((qxprime + qdTotalprime) / float(2)) + (np.multiply(qdTotalprime, qxprime) / float(3)))
    qxFinal = np.multiply(qxprime, 1 - ((qdTotalprime + qbprime) / float(2)) + (np.multiply(qdTotalprime, qbprime) / float(3)))
    qwFinal = np.multiply(qwprime, np.multiply(1 - qdTotalFinal, np.multiply(1 - qxFinal, 1 - qbFinal)))

    qdTotalFinal = qdTotalFinal.reset_index(drop=True)
    qbFinal = qbFinal.reset_index(drop=True)
    qwFinal = qwFinal.reset_index(drop=True)
    qxFinal = qxFinal.reset_index(drop=True)

    #assume Proportion of lapse at year end (%) =  1 / premiummode
    # Write Assumptions to Excel File
    # Output Final Decrement Rates Assumps as CSV
    if OutputAssumps:
        Names = ['IncTotal', 'Lapse', 'Mort', 'OB', 'qdTotalprime', 'qxprime', 'qwprime', 'qbprime',
                 'qdTotalFinal', 'qxFinal', "qwFinal", 'qbFinal']
        AssumData = pd.DataFrame([qdTotal.values, qw.values, qx.values, qb.values, qdTotalprime.values, qxprime.values,
                                  qwprime.values, qbprime.values, qdTotalFinal.values, qxFinal.values,
                                  qwFinal.values, qbFinal.values], index=Names)
        AssumData.index.name = "Month"
        AssumData.columns = AssumData.columns + 1
        pd.DataFrame.to_csv(AssumData, OutputFolder +'Final Decrement Rates.csv')

    FinalDecrRates = pd.DataFrame(np.array([qdTotalFinal, qwFinal, qxFinal, qbFinal]),
                                  index=['Final IncTotal', 'Final Lapse', 'Final Mort', 'Final OB']).transpose()
    return FinalDecrRates

xw.App.screen_updating = False
xw.App.EnableEvents = False
xw.App.display_alerts = False
# xw.App.calculation = 'manual'

# keep track of runtime
CurTime = datetime.now()
ElapseStart=datetime.now()
print 'Start'
print datetime.now() - CurTime

# Link to Excel Workbook
wb = xw.Book('LTC_Calculator.xlsb')

# Output switches
OutputBE = wb.sheets['Control'].range('out_BackEnd_tbls').value == "Yes"
OutputDec = wb.sheets['Control'].range('out_decrements').value == "Yes"
OutputALR = wb.sheets['Control'].range('out_ALR_cals').value == "Yes"
OutputX = wb.sheets['Control'].range('out_X_BE').value == "Yes"
OutputAtIssue = wb.sheets['Control'].range('out_atissue').value == "Yes"
OutputAssumps = wb.sheets['Control'].range('out_assumptions').value == "Yes"
OutputPVs = wb.sheets['Control'].range('pv_outputs').value == "Yes"
OutputExcel = wb.sheets['Control'].range('out_Excel').value == "Yes"


def GetTotalDecrements(Mode, FinalDecrRates, TotalRec, TotalInc, TotalDL_Mort, OutputFolder):

    qdTotalFinal = FinalDecrRates['Final IncTotal']
    qwFinal = FinalDecrRates['Final Lapse']
    qxFinal = FinalDecrRates['Final Mort']
    qbFinal = FinalDecrRates['Final OB']

    # Initialize Variables for Decrement calculations.
    ProjLen = 1020 # length of projection in months
    # ProjLen = int(wb.sheets['Control'].range('max)months').value) # length of projection in months

    AL_BOM = 1000.0 * np.ones(ProjLen)
    AL_BOY = 1000.0 * np.ones(ProjLen) # Active life exposure for incurrals (does not account for recoveries throughout the year)
    AL_BOM_Inc = 1000.0 * np.ones(ProjLen) # Active life exposure for incurrals (does not account for recoveries throughout the year)
    AL_BOM_Rec = np.zeros(ProjLen)
    # month of premium payment, with recoveries

    AL_Mort = 1000.0 * np.zeros(ProjLen)
    AL_OB = 1000.0 * np.zeros(ProjLen)
    AL_Lapse = 1000.0 * np.zeros(ProjLen)
    Inc = TotalInc
    Rec =  TotalRec
    AL_EOM = 1000.0 * np.ones(ProjLen)

    DL_BOM =  1000.0 * np.zeros(ProjLen)
    DL_Mort =  TotalDL_Mort
    DL_EOM = 1000.0 * np.zeros(ProjLen)

    AL_BOM[0] = 1000.0
    AL_BOY[0] = 1000.0

    FinalInc = qdTotalFinal
    FinalMort = qxFinal
    FinalOB = qbFinal
    FinalLapse = qwFinal

    for i in range(ProjLen):
        # i is in months
        month_i = (i % 12) + 1
        year_i = (i / 12) + 1
        AttAge_i = (i / 12)

        if i > 0:
            AL_BOM[i] = np.maximum(float(0), AL_EOM[i-1])
            DL_BOM[i] = np.maximum(float(0), DL_EOM[i-1])
            AL_BOM_Rec[i] = np.maximum(float(0), AL_BOM_Rec[i-1] + Rec[i-1])

            if month_i == 1:
                AL_BOY[i] = AL_EOM[i-1]
                AL_BOM_Inc[i] = AL_EOM[i-1]
            else:
                AL_BOY[i] = AL_BOY[i-1]
                AL_BOM_Inc[i] = np.maximum(float(0), AL_BOM[i - 1] - AL_OB[i - 1] - AL_Mort[i - 1] - AL_Lapse[i - 1] - Inc[i - 1])  # NO RECOVERIES

        AL_Mort[i] = AL_BOM[i] * FinalMort[min(i, len(FinalMort)-1)]
        AL_OB[i] = AL_BOM[i] * FinalOB[min(i, len(FinalOB)-1)]
        # AL_Lapse[i] = (AL_BOM_Inc[i] * FinalLapse[min(i, len(FinalLapse)-1)] * (1/float(Mode))) + \
        #               (AL_BOM_Rec[i] * FinalLapse[min(i, len(FinalLapse)-1)] * (1/float(Mode))) # separate pools for recoveries + no recoveries
        AL_Lapse[i] = AL_BOM[i] * FinalLapse[min(i, len(FinalLapse)-1)] * (1/float(Mode))
        # AL_Lapse[i] = AL_BOM_Lapse[i] * FinalLapse[min(i, len(FinalLapse)-1)] * (1/float(Mode))
        Inc[i] = AL_BOM_Inc[i] * FinalInc[min(i, len(FinalInc)-1)]

        AL_EOM[i] = max(AL_BOM[i] - AL_OB[i] - AL_Mort[i] - AL_Lapse[i] - Inc[i] + Rec[i], 0)
        DL_EOM[i] = max(DL_BOM[i] + Inc[i] - Rec[i] - DL_Mort[i], 0)

    aDec_Names = ['AL_BOM', 'AL_BOY', 'AL_BOM_Rec', 'AL_BOM Inc', 'AL Mort', 'AL OB', 'Lapse', 'Inc', 'Rec',
                  'AL_EOM', 'DL_BOM', 'Incidence', 'Recovery', 'DL_Mort', 'DL_EOM']
    aDecr = pd.DataFrame([AL_BOM, AL_BOY, AL_BOM_Rec, AL_BOM_Inc, AL_Mort, AL_OB, AL_Lapse, Inc,
                          Rec, AL_EOM, DL_BOM, Inc, Rec, DL_Mort, DL_EOM], index=aDec_Names)

    aDecrOut = aDecr.transpose()
    aDecrOut.index = aDecrOut.index + 1
    pd.DataFrame.to_csv(aDecrOut, OutputFolder + 'TotalFinalDecrements.csv')

    return aDecr.transpose()

def GetOutputs(PolNum, Internal, Type, CurPolData, OutputFolder):
    r"""Runs the various calculation scripts using the loaded policy
               data and returns the required reserve PVs and outputs
               intermediate results as required"""
    StartTime = datetime.now()

    SalTbls = CurPolData['Salvage']
    Terms = CurPolData['Term']
    CurPolDataAtIssue = CurPolData['AtIssue']

    if 'Lapse_skew' in CurPolData.keys():
        Lapse_skew = CurPolData['Lapse_skew']
    else:
        Lapse_skew = None

    print 'Pol Data Loaded'
    print datetime.now() - StartTime

    #initialize workbook
    Instance = wb.app
    Instance.calculate()
    ind_NH = wb.sheets['Control'].range('ind_NH').value == 'Y'
    ind_HHC = wb.sheets['Control'].range('ind_HHC').value == 'Y'
    ind_ALF = wb.sheets['Control'].range('ind_ALF').value == 'Y'

    # Initialize model variables
    InitMnth_dur = int(wb.sheets['Control'].range('Pol_Mon').value)
    InitPol_Yr = int(wb.sheets['Control'].range('Pol_Year').value) + (2 if InitMnth_dur == 12 else 1)
    Init_Pol_dur = int(wb.sheets['Control'].range('Init_Pol_dur').value)
    InitAttAge = int(wb.sheets['Control'].range('AttAge').value)
    InitAttainedAge = InitAttAge + (1 if InitMnth_dur == 12 else 0)
    Product = wb.sheets['Control'].range('Product').value
    proj_start_date = wb.sheets['Control'].range('proj_start_date').value
    iss_date = wb.sheets['Control'].range('iss_date').value

    # Calls Interest script which returns DataFrame of monthly interest data
    # IntData = Interest.CallMonthlyInt(iss_date, CurPolData['Interest'], Internal, OutputFolder)
    ValInt = CurPolData['AtIssue']['Interest'].iloc[0]

    #Calculations per cause
    causes = []
    if ind_NH:
        causes.append('NH')
    if ind_HHC:
        causes.append('HHC')
    if ind_ALF:
        causes.append('ALF')

    BEData_dict = {}
    WoPData_dict = {}
    ALR_dict = {}

    FinalOutputs = []

    # Get final decrement rates
    FinalDecrRates = GetDecrRates(CurPolDataAtIssue, Lapse_skew, OutputFolder)

    for cause in causes:
        cause_BP = eval("wb.sheets['Control'].range('BP_" + cause + "').value")
        cause_EP = eval("wb.sheets['Control'].range('EP_" + cause + "').value")

        # 1. Call Backend Script,  returns dictionary with: BenX, Decr
        #       BenX: a column vector containing the Benefit Claims information
        #       Decr: a dataframe containing the output associated with the Decrements

        #BEData_dict[cause]: DecTab, DecRates, BenX
        #       DecTab:     pd dataframe of [AL_BOM, AL_BOY, AL_BOM_Rec, AL_BOM_Inc, AL_Mort, AL_OB, AL_Lapse, Inc, Rec, AL_EOM, DL_BOM, Inc, Rec, DL_Mort, DL_EOM]
        #       DecRates:   pd dataframe of ['Inc', 'Lapse', 'Mort', 'OB']
        #       BenX:       np array size (1020, 1020)

        BEData_dict[cause] = Backend_Stat.CallBE(cause, cause_BP, cause_EP, CurPolDataAtIssue, FinalDecrRates,
                                                 Terms['Term_' + cause], SalTbls['Salvage_' + cause], Lapse_skew,
                                                 wb, OutputBE, OutputX, OutputDec, OutputAssumps,
                                                 OutputFolder + '_' + cause + '_backend\\', False)

        # 2. Calls Waiver of Premium Script which returns DataFrame of Waiver of Premium nPx values
        premwaiver_Wpct = float(wb.sheets['Control'].range('premwaiver_Wpct_' + cause).value)
        print cause + " premwaiver_Wpct: " + str(premwaiver_Wpct)
        # WoPData_dict[cause]: np array size 1020
        WoPData_dict[cause] = WoP.CallWoP(cause, InitPol_Yr, Init_Pol_dur, InitAttainedAge, premwaiver_Wpct,
                                          BEData_dict[cause]['DecTab']['Inc'],
                                          BEData_dict[cause]['DecTab']['Rec'], wb, Internal, OutputFolder)

        # 3. Calls ALR Script and returns dataframe with Active life Reserve data
        if Type =="Stat":
            # ALR_dict[cause]:OutputVars by month (1020)
            ALR_dict[cause] = ALR_Stat.CallALR(cause, CurPolDataAtIssue, BEData_dict[cause]['BenX'],
                                               WoPData_dict[cause], ValInt, BEData_dict[cause]['DecTab'], FinalDecrRates,
                                               wb, OutputALR, OutputFolder, True, None)

        print cause + ' BE, WoP Finished'

        MonSinceIss = wb.sheets['Control'].range("MonthsSinceIss").value + 1
        cause_FinalOutput = [cause, PolNum,
                        float(ALR_dict[cause]['PV Gross Prem Cal'][MonSinceIss]),
                        float(ALR_dict[cause]['PV Val Prem Cal'][MonSinceIss]),
                        float(ALR_dict[cause]['PV DB Cal'][MonSinceIss]),
                        float(ALR_dict[cause]['PV ROP Cal'][MonSinceIss]),
                        float(ALR_dict[cause]['PV ROP Surv Cal'][MonSinceIss]),
                        float(ALR_dict[cause]['PV UEROP Cal'][MonSinceIss]),
                        float(ALR_dict[cause]['ALR Cal'][MonSinceIss]),
                        float(ALR_dict[cause]['Val Premium per 100 Vol'].max())] # taking the "max" since Val Prem is either 0 or
                                                                    # a constrant amount when there is premium payment
        FinalOutputs.append(cause_FinalOutput)

    FinalOutputs_df = pd.DataFrame(FinalOutputs, columns=['Cause', 'Policy ID', 'PV Gross Prem Cal', 'PV Val Prem Cal',
                                                          'PV DB Cal', 'PV ROP Cal', 'PV ROP Surv Cal', 'PV UEROP Cal',
                                                          'ALR Cal', 'Val Premium per 100 Vol'])
    pd.DataFrame.to_csv(FinalOutputs_df, OutputFolder + '____PV Final Outputs per Cause.csv')

    FinalOutput_total = [FinalOutputs_df['PV Gross Prem Cal'].sum(),
                         FinalOutputs_df['PV Val Prem Cal'].sum(),
                         FinalOutputs_df['PV DB Cal'].sum(),
                         FinalOutputs_df['PV ROP Cal'].sum(),
                         FinalOutputs_df['PV ROP Surv Cal'].sum(),
                         FinalOutputs_df['PV UEROP Cal'].sum(),
                         FinalOutputs_df['ALR Cal'].sum(),
                         FinalOutputs_df['Val Premium per 100 Vol'].sum()]

    # ***********************************************************************
    # ***********************************************************************
    # ***********************************************************************
    #Combine causes
    BenX_dict = {}
    DecrLives_dict = {}
    TotalBenX = np.zeros((1020, 1020))
    TotalRec = np.zeros(1020)
    TotalInc = np.zeros(1020)
    TotalDL_Mort = np.zeros(1020)
    TotalEPAdj = np.ones(1020)

    for cause in causes:
        DecrLives_dict[cause] = BEData_dict[cause]['DecTab']
        BenX_dict[cause] = BEData_dict[cause]['BenX']
        TotalBenX = np.add(TotalBenX, BEData_dict[cause]['BenX'])
        TotalEPAdj = np.multiply(TotalEPAdj, WoPData_dict[cause])
        TotalRec = np.add(TotalRec, BEData_dict[cause]['DecTab']['Rec'])
        TotalInc = np.add(TotalInc, BEData_dict[cause]['DecTab']['Inc'])
        TotalDL_Mort = np.add(TotalDL_Mort, BEData_dict[cause]['DecTab']['DL_Mort'])

    pd.DataFrame.to_csv(pd.DataFrame(TotalBenX), OutputFolder + 'Total____BenX.csv')
    pd.DataFrame.to_csv(pd.DataFrame(TotalEPAdj), OutputFolder + 'Total____EPAdj.csv')
    pd.DataFrame.to_csv(pd.DataFrame(TotalRec), OutputFolder + 'Total___Rec.csv')
    pd.DataFrame.to_csv(pd.DataFrame(TotalInc), OutputFolder + 'Total___Inc.csv')
    pd.DataFrame.to_csv(pd.DataFrame(TotalDL_Mort), OutputFolder + 'Total___DLMort.csv')

    # Premium mode
    prem_mode = int(wb.sheets['Control'].range('prem_mode').value)
    if prem_mode == 3:
        Mode = 4
    elif prem_mode == 4:
        Mode = 12
    else:
        Mode = prem_mode

    TotalDecrements = GetTotalDecrements(Mode, FinalDecrRates, TotalRec, TotalInc, TotalDL_Mort, OutputFolder)
    TotalALR = ALR_Stat.CallALRTotal("Total", causes, CurPolDataAtIssue, TotalBenX, TotalEPAdj, ValInt, TotalDecrements,
                                FinalDecrRates, wb, OutputALR, OutputFolder, True, None, BenX_dict, DecrLives_dict)

    MonSinceIss = wb.sheets['Control'].range("MonthsSinceIss").value + 1
    PolicyTestNum = wb.sheets['Control'].range("PolicyTestNum").value
    TotalFinalOutput = [PolicyTestNum, "TOTAL", PolNum,
                        float(TotalALR['PV Gross Prem Cal'][MonSinceIss]),
                        float(TotalALR['PV Val Prem Cal'][MonSinceIss]),
                        float(TotalALR['PV DB Cal'][MonSinceIss]),
                        float(TotalALR['PV ROP Cal'][MonSinceIss]),
                        float(TotalALR['PV ROP Surv Cal'][MonSinceIss]),
                        float(TotalALR['PV UEROP Cal'][MonSinceIss]),
                        float(TotalALR['ALR Cal'][MonSinceIss]),
                        (float(TotalALR['ALR Cal'][MonSinceIss]) / (1 + (float(TotalALR['BOPM Dis Lives'][MonSinceIss]) / 1000.0))),
                        float(TotalALR['Val Premium per 100 Vol'].max())] # taking the "max" since Val Prem is either 0 or a constant amount when there is premium payment
    TotalFinalOutputs = []

    TotalFinalOutputs.append(TotalFinalOutput)
    TotalFinalOutputs_df = pd.DataFrame(TotalFinalOutputs, columns=['#', 'Cause', 'Policy ID', 'PV Gross Prem Cal', 'PV Val Prem Cal',
                                                          'PV DB Cal', 'PV ROP Cal', 'PV ROP Surv Cal', 'PV UEROP Cal',
                                                          'ALR Cal', 'Adj ALR', 'Val Premium per 100 Vol'])
    pd.DataFrame.to_csv(TotalFinalOutputs_df, OutputFolder + '_____Total____FINAL OUTPUT.csv')
    print datetime.now() - StartTime
    print 'ALR Finished'
    return TotalFinalOutputs


def RunPolicy(Internal, Type, OutputFolder):
    r"""Uses loaded data to perform reserve calculation by
                joining together various scripts."""
    StartTime = datetime.now()
    print 'Start'
    print datetime.now() - StartTime

    # Links to WB Instance (used for calculating workbook)
    Instance = wb.app
    Instance.calculate()
    # Get Runtype,  number of policies in inforce,  initial Record Number cell,
    # Make array of policies run indicator
    #RunType = wb.sheets['Control'].range('inforce_type').value

    numPolicies = int(wb.sheets['PoliciesList'].range('numPolicies').value)
    PolicyTestNum = int(wb.sheets['Control'].range('PolicyTestNum').value)
    # OutRuns = np.array(wb.sheets['Extract_ILTC'].range("A3" + ":A" + str(3 + numPolicies)).value)
    Records = np.array(wb.sheets['PoliciesList'].range("TestPolicy1").expand('down').value)
    PolicyID = wb.sheets['Control'].range('PolicyID').value

    print "Get Policy Info"
    
    # Out = pd.DataFrame(np.zeros(11))
    # counter = 0

    Instance.calculate()
    print "running pol: " + str(PolicyTestNum) + " ID: " + str(wb.sheets['Control'].range('pol_id').value)


    CurPolData = A_Load.load_assumptions()
    Output = GetOutputs(str((Records[PolicyTestNum-1])), Internal, Type, CurPolData, OutputFolder)
    # Load Assumptions for current policy
    # try:
    #     CurPolData = A_Load.load_assumptions()
    #     Output = GetOutputs(str((Records[PolicyTestNum-1])), Internal, Type, CurPolData, OutputFolder)
    # except Exception as e:
    #     print "ERROR:"
    #     print(e)
    #     Output = ['N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A']

    OutputExcel = wb.sheets['Control'].range('out_Excel').value == "Yes"
    
    # Writes output to the Excel file
    """Display on Output sheet"""
    if OutputExcel:
        # wb.sheets['Output'].range("OutputStart").end('down').offset(1,0).value = pdOUT.values
        wb.sheets['Output'].range("OutputStart").end('down').offset(1, 0).value = Output
    ElapseEnd = datetime.now()
    # wb.sheets['Control'].range("elapsed").value = ( ElapseEnd - ElapseStart).total_seconds()

def Caller():
    start = datetime.now()

    # Links to WB Instance (used for calculating workbook)
    Instance = wb.app
    Instance.calculate()

    path_output = wb.sheets['Control'].range("path_output").value

    #------------------------------------------
    # Loop policy runs
    #------------------------------------------
    TestMultPolicies = wb.sheets['Control'].range("TestMultPolicies").value == "Y"
    TestPolNum_start = int(wb.sheets['Control'].range("TestPolNum_start").value)
    TestPolNum_end = int(wb.sheets['Control'].range("TestPolNum_end").value)

    if not TestMultPolicies:
        TestPolNum_start = int(wb.sheets['Control'].range("PolicyTestNum").value)
        TestPolNum_end = int(wb.sheets['Control'].range("PolicyTestNum").value)


    for i_pol in range(TestPolNum_start, TestPolNum_end+1):
        wb.sheets['Control'].range("PolicyTestNum").value = i_pol
        PolicyTestNum = i_pol

        wb.app.calculate()
        PolicyID = wb.sheets['Control'].range('PolicyID').value
        #PolicyTestNum = int(wb.sheets['Control'].range('PolicyTestNum').value)

        output_path = path_output + str(PolicyTestNum) + '-' + str(PolicyID) + '\\'
        MakeDir(output_path)
        OutputFolder = output_path + str(PolicyTestNum) + '-' + str(PolicyID) + '_'

        #if wb.sheets['Control'].range('switch_reservetype').value == "Stat":
        Type = "Stat"
        print "Running Stat"
        RunPolicy(False, Type, OutputFolder)
        " Time used for run "
        diff = datetime.now() - start
        Hours = (diff.seconds) / 3600
        minutes = (diff.seconds % 3600) / 60
        seconds = int(((diff.seconds % 3600) / float(60) - minutes) * 60)
        wb.sheets['Control'].range('OutputStatus').value = str(Hours) + ' : ' + str(minutes) + ' : ' + str(seconds)
        # xw.App.screen_updating = True
        xw.App.calculation = 'automatic'
    #------------------------------------------
    """Turn on screen updating, displays and calculation at the endof run"""
    #xw.App.EnableEvents = True
    #xw.App.display_alerts = True



    # RunPolicy(True)
    #
    #
    # Type = "Stat"
    # print "Running Stat"
    # RunPolicy(True, Type, )
    #
    # end = datetime.now()
    # print 'Total Time:'
    # print end - CurTime
