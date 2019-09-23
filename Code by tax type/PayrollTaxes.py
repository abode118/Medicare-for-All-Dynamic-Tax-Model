#Payroll Tax functions for Medicare for All Project
"""
Created on Sat Sep 21 10:40:13 2019

@author: abode
"""

import csv
import numpy
import copy
import MFAvariables as m
import IncomeTaxes as i


"""
2019 Payroll Tax Info: [OASDI rate, OASDI cap, HI rate, addt'l HI rate, threshold dictionary]
"""
PayrollTaxin19 = [0.124,132900, 0.029,0.009,
                  {'Single': 200000,
                   'Married filed jointly + Surviving Spouses':250000,
                   'Married filed separately': 125000,
                   'HoH':200000}]

"""
Function: create a dictionary of payroll tax data

Inputs: PayrollFile, a csv file

Output: dictionary, format below
{year:
    cap,
    OASDItax rate,
    OASDI collected
    HI tax rate,
    addt'l HI tax rate,
    Upper HI Threshold (Indiv),
    Upper HI Threshold (Married Joint),
    Upper HI Threshold (Married Separate),
    HI collected}
"""

def CreatePayrollTaxDict(PayrollFile):
    with open(PayrollFile) as f:
        PayrollTaxList = list(list(yr) for yr in csv.reader(f, delimiter=','))
        f.close()
    DictPayrollTax = {}
    for yr in PayrollTaxList[1:]:
        for r in range(1,12):
            if '0.' in yr[r]:
                yr[r] = int(yr[r].replace('0.',''))/10000
                #convert rates to percents
            else:
                yr[r] = int(yr[r])
        DictPayrollTax[str(yr[0])] = [yr[1],yr[2],yr[10],yr[3],yr[7],
                       yr[4],yr[5],yr[6],yr[11]]
    return DictPayrollTax

"""
Function: create new payroll list, preserving current OASDI rate

Inputs:
    oldpayrolllist, a list
    newHIrates, a list (new HI and addtl HI rate)
    
Output: list, updated for new HI rates
[OASDI rate, OASDI cap, HI rate, addt'l HI rate, threshold dictionary]   
"""

def newpayrolllist(oldpayrolllist,newHIrates):
    newlist = copy.deepcopy(oldpayrolllist)
    newlist[2] = newHIrates[0]
    newlist[3] = newHIrates[1]
    return newlist

"""
Function: Calculating % of income in diff filing statuses, to be used to 
project Payroll Tax revenue changes

Inputs:
    incomedistribution, a list of lists
    FilingStatus, a dictionary
    
Output: dictionary, format below
{Filing Status:
    [revenue from status,
    % of total revenue from status]}
"""

def statusdistribution(incomedistribution,FilingStatus):
    #initiate a dictionary which will resemble {Status: rev from status}, and
    #initiate a rev from each status of 0
    statusdistro = {}
    totrev = 0
    for status in FilingStatus:
        statusdistro[status] = 0
        
    for line in incomedistribution:
        if line[0] in FilingStatus: 
            #weed out the "Total" etc lines, to avoid duplication
            status = str(line[0])
            statusdistro[status] = statusdistro[status] + line[4]
            totrev += line[4]
            #add total AGI from this line to the current rev from status
    for st in statusdistro:
        statusdistro[st] = [statusdistro[st],statusdistro[st]/totrev]
        #when complete, switch dictionary to resemble {Status: [rev from status,
        #% of total rev from status]}
    return statusdistro  

"""
Function: project payroll tax revenue, with no changes

Inputs:
    PayrollTaxFile, a csv file
    BaseYear, an int
    StartYear, an int (> 2019)
    Years, an int
    Inflation, a float
    PopulationGrowth, a float
    
Output: list of lists (array) of [OASDI revenue, HI revenue] for each year
"""    

def ProjectPayrollTaxSimple(PayrollTaxFile,BaseYear,StartYear,Years,Inflation,
                      PopulationGrowth):

    #create payroll tax dictionary and pull out the OASDI and HI rev in base year
    DictPayrollTax = CreatePayrollTaxDict(PayrollTaxFile)
    OASDItaxrev = DictPayrollTax[str(BaseYear)][2]
    HItaxrev = DictPayrollTax[str(BaseYear)][8]
    
    #update from base year to start year, using inflation and population growth
    for y in range(StartYear-BaseYear):
        OASDItaxrev = OASDItaxrev * (1 + PopulationGrowth) * (1 + Inflation)
        HItaxrev = HItaxrev * (1 + PopulationGrowth) * (1 + Inflation)
            
    PayrollTaxRevSimple = []
    for j in range(Years):       
        PayrollTaxRevSimple.append([OASDItaxrev,HItaxrev])
        #update for inflation and population growth    
        OASDItaxrev = OASDItaxrev * (1 + PopulationGrowth) * (1 + Inflation)
        HItaxrev = HItaxrev * (1 + PopulationGrowth) * (1 + Inflation)
    
    PayrollTaxRevSimple = numpy.array(PayrollTaxRevSimple)
    
    return PayrollTaxRevSimple

"""
Function: Projecting payroll taxes; with rate change(s)

Inputs:
    IncomeTaxFile, a csv file
    PayrollTaxFile, a csv file
    CurrentPayrollTaxList, a list
    NewPayrollTaxList, a list
    FilingStatus, a dictionary
    BaseYear, an int (2000 - 2016; historical data available for income groups)
    StartYear, an int (>2019)
    Years, an int
    Inflation, a float
    PopulationGrowth, a float

Output: list of lists (array) of [OASDI revenue, HI revenue] for each year
"""

def ProjectPayrollTaxHI(IncomeTaxFile,PayrollTaxFile,CurrentPayrollTaxList,
                      NewPayrollTaxList,FilingStatus,BaseYear,StartYear,Years,
                      Inflation,PopulationGrowth):

    DictIncomeTax = i.CreateIncomeTaxDict(IncomeTaxFile)
    incomedistribution = m.createfulldistribution(DictIncomeTax,BaseYear)
    statdistribution = statusdistribution(incomedistribution,FilingStatus)
    DictPayrollTax = CreatePayrollTaxDict(PayrollTaxFile)
    NewHIThresholdDict = NewPayrollTaxList[4]
    
    #initiate starting OASDI and HI tax revs, using Base Year's rev data
    OASDItaxrev = DictPayrollTax[str(BaseYear)][2]
    HItaxrev = DictPayrollTax[str(BaseYear)][8]
    
    """
    We need to determine how much AGI is impacted by the additional HI rate
    Depends on filing status and corresponding threshold
    
    abovebelow is a dictionary of form:
        {status:
            [HI below threshold, HI above threshold],
            [HI % below threshold, HI % above threshold]
            [rev from status in Base Year, % of total rev from status in Base Year]]
            }
    
    loop through incomedistribution to calculate % of rev within each filing
    status that is above/below the OASDI and HI cap/threshold for the given status
    """

    abovebelow = {}
    for s in FilingStatus:
        abovebelow[s] = [[0,0],[0,0],statdistribution[s]]
    for line in incomedistribution:
        status = str(line[0])
        if status in FilingStatus:
            
            current = abovebelow[status]
            threshold = NewHIThresholdDict[status]
            avgAGI = line[2]
            minAGI = line[3][0]
            maxAGI = line[3][1]
            pplperdoll = line[3][3]
            totAGI = line[4]
            
            if threshold > minAGI and threshold < maxAGI:
                avglist = m.find_averages(avgAGI,minAGI,maxAGI,pplperdoll,threshold)
                #if the threshold falls between the low and high of income
                #group, calculate two new averages on either side
                #returns [newlowavg, numppl],[newhighavg,numppl]
                current[0][0] += avglist[0][0] * avglist[0][1]
                current[0][1] += avglist[1][0] * avglist[1][1]
                #multiply result to calc total AGI above/below threshold
                #add to below cap and above cap, as applicable
                
            elif threshold > maxAGI:
                current[0][0] += totAGI
                #else, if the threshold is above the max AGI, add totAGI to
                #"below threshold"
                
            else:
                current[0][1] += totAGI
                #else (threshold < min AGI), add totAGI to "above threshold"
                
        #now reset the percentages using your newly updated income totals
        allAGI = current[0][0] + current[0][1]
        current[1] = [current[0][0]/totAGI, current[0][1]/allAGI]
        abovebelow[status] = current
    
    """
    Now we can project future payroll tax revenue, knowing how much AGI is
    impacted by a change in rate
    """
    #estimate the total income pool; divide by HIrate + (addt'l % multiplied by
    #% of income subject to addt'l % (i.e. divide by the effective HI tax rate)
    abovethresholdpct = 0
    for status in abovebelow:
        abovethresholdpct += abovebelow[status][1][1] * abovebelow[status][2][1]
    HItotrev = HItaxrev/(CurrentPayrollTaxList[2]+(CurrentPayrollTaxList[3]*abovethresholdpct))
   
    #update revenue from base year to start year, using inflation and population growth
    for y in range(StartYear-BaseYear):
        OASDItaxrev = OASDItaxrev * (1 + PopulationGrowth) * (1 + Inflation)
        HItaxrev = HItaxrev * (1 + PopulationGrowth) * (1 + Inflation)
        HItotrev = HItotrev * (1 + PopulationGrowth) * (1 + Inflation)
    
    #if HI rate changed, multiply the change by the total rev and adjust
    if NewPayrollTaxList[2] != CurrentPayrollTaxList[2]:
        HItaxrev += (NewPayrollTaxList[2] - CurrentPayrollTaxList[2]) * HItotrev
        
    #if addt'l HI rate changed, multiply the change * the % of income
    #above the threshold (for applicable filing status) * total rev and adjust
    if NewPayrollTaxList[3] != CurrentPayrollTaxList[3]:
        abovethresholdpct = 0
        for l in abovebelow:
            abovethresholdpct += abovebelow[i][1][1] * abovebelow[i][2][1]
        HItaxrev += (NewPayrollTaxList[3] - CurrentPayrollTaxList[3]) * abovethresholdpct * HItotrev
                
    PayrollTaxRev = []
    for j in range(Years):               
        PayrollTaxRev.append([OASDItaxrev,HItaxrev])
        
        #update from start to end, using inflation and population growth
        OASDItaxrev = OASDItaxrev * (1 + PopulationGrowth) * (1 + Inflation)
        HItaxrev = HItaxrev * (1 + PopulationGrowth) * (1 + Inflation)
        HItotrev = HItotrev * (1 + PopulationGrowth) * (1 + Inflation)
    
    PayrollTaxRev = numpy.array(PayrollTaxRev)
    
    return PayrollTaxRev

"""
Function: raising Payroll Tax rates

Inputs:
    CurrentPayrollList, a list
    incrementHI, a float
    incrementaddtl, a float

Output: a new payroll tax list, format below
[OASDI rate, OASDI cap, HI rate, addt'l HI rate, threshold dictionary]
"""

def raisepayrolltaxes(CurrentPayrollList,incrementHI,incrementaddtl):
    newHIrates = [round(CurrentPayrollList[2] + incrementHI,4),
                  round(CurrentPayrollList[3] + incrementaddtl,4)]
    NewPayrollTaxList = newpayrolllist(CurrentPayrollList,newHIrates)
    return NewPayrollTaxList

"""
Function: determine effective payroll tax rate in a given year for a person
with a given AGI and status

Inputs:
    Year, an int
    Income, an int
    Status, a string (in FilingStatus)
    PayrollTaxList, a list
    Inflation, a float

Output: effective tax rate, a float
"""

def effectivepayrolltax(Year,Income,Status,PayrollTaxList,Inflation):
    
    PayrollTaxesPaid = 0
    HIthresholds = PayrollTaxList[4]
    #mypayrollist is a list of [OASDIrate,OASDIcap,HIrate,addtlHIrate,
    #my addtlHI threshold]
    mypayrolllist = [PayrollTaxList[0],PayrollTaxList[1],PayrollTaxList[2],
                     PayrollTaxList[3],HIthresholds[Status]]
    
    #adjust threshold for inflation since 2019
    for y in range(Year-2019):
        mypayrolllist[4] = mypayrolllist[4] * (1 + Inflation)
    
    #if income > OASDI cap, multiply OASDI rate by OASDI cap and divide by two
    #(to adjust for 1/2 paid by employer, 1/2 by employee)
    #otherwise, multiply income by OASDI rate and divide by two
    if Income > mypayrolllist[1]:
        PayrollTaxesPaid += (mypayrolllist[0] * mypayrolllist[1])/2
    else:
        PayrollTaxesPaid += (mypayrolllist[0] * Income)/2
    
    #if income > HI threshold, multiply addtl HI rate by income above threshold
    if Income > mypayrolllist[4]:
        PayrollTaxesPaid += (mypayrolllist[3] * (Income - mypayrolllist[4]))
    
    #multiply HI rate by income and divide by two
    PayrollTaxesPaid += (mypayrolllist[2] * Income)/2
    
    if Income == 0:
        return 0
    else:
        return round(PayrollTaxesPaid/Income,4)