"""
Created on Sat Sep 21 10:48:01 2019

@author: abode
"""

import csv

"""
******************************************************************************
FUNCTIONS NEEDED TO PROJECT CORPORATE TAX REVENUE
******************************************************************************
"""

"""
******************************************************************************
PROJECTCORPORATETAX()

Function: Projecting corporate tax, given a current rate and new rate (can be
the same, if you're looking for a current state projection)

Inputs:
    FedRevFile, a csv file
    BaseYear, an int
    StartYear, an int
    Years, an int
    CurrentCorpTaxRate, a float
    NewCorpTaxRate, a float
    Inflation, a float
    GDPGrowth, a float

Output: a list of corporate tax revenue
******************************************************************************
"""
def ProjectCorporateTax(FedRevFile,BaseYear,StartYear,Years,CurrentCorpTaxRate,
                        NewCorpTaxRate,Inflation,GDPGrowth):
    FedRevDict = CreateFedRevDict(FedRevFile)
    CorpTaxes = FedRevDict['Corporation Income Taxes'][str(BaseYear)]
    CorpIncome = CorpTaxes / CurrentCorpTaxRate
    
    for i in range(StartYear-BaseYear):
        CorpIncome = CorpIncome * (1 + GDPGrowth)
        CorpIncome = CorpIncome * (1 + Inflation)

    CorpTaxRev = []
    for j in range(Years):
        CorpTaxRev.append(CorpIncome * NewCorpTaxRate)
        CorpIncome = CorpIncome * (1 + GDPGrowth)
        CorpIncome = CorpIncome * (1 + Inflation)
        
    return CorpTaxRev


"""
******************************************************************************
HELPER CODE
******************************************************************************
"""


"""
******************************************************************************
CREATEFEDREVDICT()

Function: create dictionary of dictionaries for Federal Revenue Data by Year;
note that 2019-2024 are estimates

Inputs:
    RevFile, a csv file
Output: dictionary of dictionaries, format below:
{RevenueBucket:
    Year:
        Revenue}
******************************************************************************
"""
def CreateFedRevDict(RevFile):
    with open(RevFile) as f:
        FedRevList = list(list(yr) for yr in csv.reader(f, delimiter=','))
        f.close()
    DictFedRev = {}
    for i in range(1,4):
        DictFedRev[FedRevList[0][i]] = {}
    for yr in FedRevList[1:]:
        for i in range(1,4):
            yr[i] = int(yr[i])
            DictFedRev[FedRevList[0][i]][str(yr[0])] = yr[i]
    return DictFedRev

"""
******************************************************************************
RAISECORPORATETAX()

Function: raise corporate tax rate

Inputs:
    CurrentCorpTaxRate, a float
    increment, a float

Output: new corporate tax rate (current + increment), a float
******************************************************************************
"""
def RaiseCorporateTax(CurrentCorpTaxRate,increment):
    return round(CurrentCorpTaxRate + increment,4)
