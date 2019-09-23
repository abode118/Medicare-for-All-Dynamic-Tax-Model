#Essential variables/functions for Medicare for All Project
"""
Created on Sat Sep 21 10:29:00 2019

@author: abode
"""

"""
Initiate Variables
"""

TotalCost = 30000000000000
TotalYears = 10
DesiredCoverage = 0.50

#growth rate assumptions
Inflation = 0.018
PopulationGrowth = 0.007
GDPGrowth = 0.015

#current rates
CurrentCorpTaxRate = 0.21
OASDItax = 0.124
HItax = 0.029
addtlHItax = 0.009

FilingStatus = ['Single','Married filed jointly + Surviving Spouses',
                'Married filed separately','HoH']

StandardDeduction = {'Single':12200,
                     'Married filed jointly + Surviving Spouses':24400,
                     'Married filed separately':12200,
                     'HoH':18350}

IncomeGroups ={
        'No adjusted gross income':[0,0],
        '$1 under $5,000':[1,5000],
        '$5,000 under $10,000':[5000,10000],
        '$10,000 under $15,000':[10000,15000],
        '$15,000 under $20,000':[15000,20000],
        '$20,000 under $25,000':[20000,25000],
        '$25,000 under $30,000':[25000,30000],
        '$30,000 under $40,000':[30000,40000],
        '$40,000 under $50,000':[50000,75000],
        '$50,000 under $75,000':[50000,75000],
        '$75,000 under $100,000':[75000,100000],
        '$100,000 under $200,000':[100000,200000],
        '$200,000 under $500,000':[200000,500000],
        '$500,000 under $1,000,000':[500000,1000000],
        '$1,000,000 under $1,500,000':[1000000,1500000],
        '$1,500,000 under $2,000,000':[1500000,2000000],
        '$2,000,000 under $5,000,000':[2000000,5000000],
        '$5,000,000 under $10,000,000':[5000000,10000000],
        '$10,000,000 or more':[10000000,10000000]}

Brackets2019Data = "C:\Python Data Files\Brackets2019.csv"
Brackets2017Data = "C:\Python Data Files\Brackets2017.csv"
FedRevData = "C:\Python Data Files\Federal Revenue.csv"
IncomeTaxData = "C:\Python Data Files\Income Taxes.csv"
PayrollTaxData = "C:\Python Data Files\Payroll Taxes.csv"

"""
Function: get distribution of people within each IncomeGroup at $1 increment

Inputs:
    minincome, an int
    maxincome, an int
    totalnumber, an int

Outputs: list of [minincome, maxincome, total number of ppl, number of ppl per $1]
"""

def createdistribution(minincome,maxincome,totalnumber):
    if maxincome == minincome:
        numperdollar = totalnumber
    else:
        numperdollar = totalnumber/(maxincome-minincome)
        
    return [minincome,maxincome,totalnumber,
            numperdollar]

"""
Function: produce distribution of people at $1 increment for each line
(filing status, year, income group) in a given Income Tax Dictionary

Inputs:
    DictIncomeTax, a dictionary
    Year, an int
    IncomeGroups, a dictionary

Output: list of lists [status,
                       income group,
                       avgAGI,
                      [minincome, maxincome, total number of ppl, number of ppl per $1],
                      totalAGI]
"""

def createfulldistribution(DictIncomeTax,Year,IncomeGroups):
    fulldistro = []
    yr = str(Year)
    for status in DictIncomeTax:
        for group in DictIncomeTax[status][yr]:
            #for each group in each year in each filing status
            if group in IncomeGroups:
                #weed out the "Total" and other types that are duplicative
                distro = createdistribution(DictIncomeTax[status][yr][group][0],
                                            DictIncomeTax[status][yr][group][1],
                                            DictIncomeTax[status][yr][group][2])
                avgAGI = DictIncomeTax[status][yr][group][4]
                fulldistro.append([status,group,avgAGI,distro,
                                   DictIncomeTax[status][yr][group][3]])
    return fulldistro

"""
Function: given a starting average, threshold, and distribution (number of ppl
per $1 increment), calculate two new averages on either side of threshold

Inputs:
    startavg, an int
    low, an int
    high, an int
    personperdoll, a float
    threshold, an int

Output: list of lists, [[new low avg and # of ppl],[new high avg and # of ppl]]
"""

def find_averages(startavg,low,high,personperdoll,threshold):
    
    #calculate number of people in each side of threshold
    lowdenom = (threshold - low) * personperdoll
    highdenom = (high - threshold) * personperdoll

    #set the new low average to midpoint between the threshold and the low
    newlowavg = (threshold + low)/2
    
    #calculate what the new high avg is, given the new low avg, num of ppl on
    #either side, and starting avg
    newhighavg = ((startavg * (high - low) * personperdoll) - (lowdenom * newlowavg)) \
                /highdenom
    return [[newlowavg,lowdenom], [newhighavg,highdenom]]

"""
Function: do your tax rate changes cover the desired % of the total cost?

Inputs:
    desiredcoverage, a float
    totalamount, an int
    coveredamount, a float

Output: Boolean
"""
def isitcovered(desiredcoverage,totalamount,coveredamount):
    if desiredcoverage * totalamount < coveredamount:
        return False
    else:
        return True