#Income Taxes for Medicare for All Project
"""
Created on Sat Sep 21 10:28:31 2019

@author: abode
"""

import csv
import MFAvariables as m
import copy

"""
Function: Create dictionary for income taxes

Input: IncomeTaxFile, a csv file

Output: Nested dictionary, format below
{filingstatus:
    year:
        IncomeGroup:
            [min AGI,
            max AGI,
            # of returns,
            total AGI,
            avg AGI,
            total taxable income,
            income tax collected]}
"""

def CreateIncomeTaxDict(IncomeTaxFile):
    #open file and convert to list of lists; close
    with open(IncomeTaxFile) as f:
        IncomeTaxList = list(list(yr) for yr in csv.reader(f, delimiter=','))
        f.close()

    DictIncomeTax = {}
    for yr in IncomeTaxList[1:]:
        for i in range(2,9):
            yr[i] = int(yr[i])
        if str(yr[9]) not in DictIncomeTax.keys():
            DictIncomeTax[str(yr[9])] = {}
            #if filing status not in dict yet, add blank dict
        if str(yr[0]) not in DictIncomeTax[str(yr[9])].keys():
            DictIncomeTax[str(yr[9])][str(yr[0])] = {}
            #if year not in filing status dict yet, add blank dict
        if yr[4] != 0:
            avgAGI = yr[5]/yr[4]
        else:
            avgAGI = 0
        DictIncomeTax[str(yr[9])][str(yr[0])][str(yr[1])] = [yr[2],yr[3],yr[4],
                      yr[5],avgAGI,yr[6],yr[8]]
    return DictIncomeTax

"""
Function: Create dictionary of dictionaries with tax brackets and income thresholds

Input: BracketFile, a csv file

Output: Nested dictionary, format below:
{Filing Status:
    Bracket (Tax Rate):
        Threshold}
"""

def CreateBracketDict(BracketFile):
    with open(BracketFile) as f:
        BracketList = list(list(i) for i in csv.reader(f, delimiter=','))
    f.close()
    DictBrackets = {}
    for i in range(1,5):
        DictBrackets[BracketList[0][i]] = {}
        #initiate empty dictionaries for each filing status
    for br in BracketList[1:]:
        for i in range(1,5):
            br[i] = int(br[i])
            #convert all string cutoffs to integers
            DictBrackets[BracketList[0][i]][str(br[0])] = br[i]
    return DictBrackets

"""
2019 Bracket Dictionary
"""

BracketDict2019 = CreateBracketDict(m.Brackets2019Data)

"""
Function: Create list of tax brackets

Input: BracketFile, a csv file

Output: list of tax brackets (floats)
"""

def CreateBracketList(BracketFile):
    with open(BracketFile) as f:
        BracketListofLists = list(list(i) for i in csv.reader(f, delimiter=','))
    f.close()
    BracketList = []
    for br in BracketListofLists[1:]:
        BracketList.append(float(br[0]))
    return BracketList

"""
Function: raise Tax Brackets and create new dictionary

Input: BracketFile, a csv file
       NewBracketsList, a list of brackets

Output: Nested dictionary, format below:
{Filing Status:
    Bracket (Tax Rate):
        Threshold}
"""

def newbracketdict(BracketFile,NewBracketsList):
    with open(BracketFile) as f:
        BracketList = list(list(i) for i in csv.reader(f, delimiter=','))
    f.close()

    #replace old brackets with corresponding bracket from NewBracketsList
    for n in range(1,len(BracketList)):
        BracketList[n][0] = str(NewBracketsList[n-1])
    
    DictBrackets = {}
    for i in range(1,5):
        DictBrackets[BracketList[0][i]] = {}
        #initiate empty dictionaries for each filing status
    for br in BracketList[1:]:
        for i in range(1,5):
            br[i] = int(br[i])
            DictBrackets[BracketList[0][i]][str(br[0])] = br[i]
    return DictBrackets

"""
Function: Project income tax revenue

Inputs:
    IncomeTaxFile, a csv file
    BracketFile, a csv file
    StandardDeduction, a dictionary
    BaseYear, an int (2000 - 2016; historical data available)
    StartYear, an int (> 2019)
    Years, an int
    Inflation, a float
    PopulationGrowth, a float

Output: a list of income tax revenue for each year from StartYear to StartYear + Years
"""

def ProjectIncomeTax(IncomeTaxFile,BracketFile,StandardDeduction,IncomeGroups,BaseYear,
                     StartYear,Years,Inflation,PopulationGrowth):

    brackets = CreateBracketDict(BracketFile)
    DictIncomeTax = CreateIncomeTaxDict(IncomeTaxFile)
    
    #take income tax dictionary and provide a distribution (number of people
    #per income dollar increment) for each income group
    incomedistribution = m.createfulldistribution(DictIncomeTax,BaseYear,IncomeGroups)
    
    #create a copy of StandardDeduction so that you can adjust thresholds for inflation
    StandDeduc = copy.deepcopy(StandardDeduction)
    
    #update AGI and income group mins/max for inflation and population growth
    #between the base year and start year
    for i in range(StartYear-BaseYear):
        for line in incomedistribution:
            line[2] = line[2] * (1 + Inflation) #adjust avg AGI
            line[3][0] = line[3][0] * (1 + Inflation) #adjust min
            line[3][1] = line[3][1] * (1 + Inflation) #adjust min
            line[3][2] = line[3][2] * (1 + PopulationGrowth) #adjust totalppl
            line[3][3] = line[3][3] * (1 + PopulationGrowth) #adjust pplperdollar
    
    #update StandDeduc and tax bracket thresholds for inflation between
    #2019 (year our variables are drawn from) to start year
    for i in range(StartYear - 2019):
        for deduc in StandDeduc:
            StandDeduc[deduc] = StandDeduc[deduc] * (1 + Inflation)
        for status in brackets:
            for br in brackets[status]:
                brackets[status][br] = round(brackets[status][br] * (1+Inflation),0)
            
    IncomeTaxRev = []
    for j in range(Years):
        thisyearrev = 0
        
        #updated StandDeduc and tax bracket thresholds for inflation each year
        for status in brackets:
            for br in brackets[status]:
                brackets[status][br] = round(brackets[status][br] * (1+Inflation),0)
        for deduc in StandDeduc:
            StandDeduc[deduc] = StandDeduc[deduc] * (1 + Inflation)
        
        for line in incomedistribution:
            #if in StandDeduc (aka, if not "Total" etc)
            status = str(line[0])
            if status in StandDeduc:
                #reset avgAGI, min, and max to account for StandardDeduction
                #applicable for said filing status                
                AGIafterdeduction = max(line[2] - StandDeduc[status],0)
                minafterdeduction = max(line[3][0] - StandDeduc[status],0)
                maxafterdeduction = max(line[3][1] - StandDeduc[status],0)
                
                previousbr = 0
                previousthreshold = 0

                #create a list of thresholds
                thresholdlist = []
                for br in brackets[status]:
                    thresholdlist.append(brackets[status][br])
                
                #for each bracket in current filing status, set threshold
                for br in brackets[status]:
                    threshold = brackets[status][br]
                    if threshold <= minafterdeduction:
                        thisyearrev += previousbr * (threshold - previousthreshold) * line[3][2]
                        #if the threshold is below the income group min after
                        #deduction, multiply prior tax rate * (current threshold
                        #minus prior threshold) * total ppl in income group
                    elif threshold < maxafterdeduction:
                        avglist = m.find_averages(AGIafterdeduction,
                                                minafterdeduction,
                                                maxafterdeduction,
                                                line[3][3],
                                                threshold)
                        thisyearrev += (avglist[0][0] - previousthreshold) * avglist[0][1] * previousbr
                        thisyearrev += ((threshold - previousthreshold) * avglist[1][1] * previousbr)
                        thisyearrev += (avglist[1][0] - threshold) * avglist[1][1] * float(br)
                        #else, if the threshold is greater than the min after
                        #deduction but less than the max after deduction,
                        #calculate two new avg AGIs on either side of threshold
                        #and multiply lower half by prior rate; multiply upper
                        #half by prior rate up to threshold, higher rate for rest
                    elif previousthreshold <= minafterdeduction:
                        thisyearrev += (AGIafterdeduction - previousthreshold) * line[3][2] * previousbr
                        #else, if the current threshold is greater than max after deduction,
                        #but the previous threshold is less than or equal to your minimum
                        #(i.e. you fell into category #1 last time but you have 
                        #remainder income) multiply this REMAINDER income by
                        #the prior tax rate
                    
                    #if the threshold is greater than the max, and your AGI no revenue is added
                    
                    previousthreshold = brackets[status][br]
                    previousbr = float(br)
                
                #if the minimum of ur income group is greater than the maximum threshold,
                #multiply this excess income by the highest tax rate
                if max(thresholdlist) < minafterdeduction:
                    thisyearrev += (AGIafterdeduction - threshold) * line[3][2] * float(br)
            
            #update AGI/min/max/numppl for inflation and population growth each year
            line[2] = line[2] * (1 + Inflation) #adjust avg AGI
            line[3][0] = line[3][0] * (1 + Inflation) #adjust min
            line[3][1] = line[3][1] * (1 + Inflation) #adjust min
            line[3][2] = line[3][2] * (1 + PopulationGrowth) #adjust totalppl
            line[3][3] = line[3][3] * (1 + PopulationGrowth) #adjust pplperdollar
            
        IncomeTaxRev.append(thisyearrev)
        
    return IncomeTaxRev

"""
Function: raising income tax brackets
    Progressive: ratio > 1
    Flat: ratio == 1

Inputs:
    currentbrlist, a list
    ratio, an int (>= 1)
    increment, a float

Output: newbrlist, a list of new brackets
"""

def raiseincometaxbrackets(currentbrlist,ratio,increment):
    newbrlist = copy.deepcopy(currentbrlist)
    for b in range(len(newbrlist)):
        if ratio == 1:
            newbrlist[b] =  round(newbrlist[b] + increment,4)
            #if your ratio is 1 (i.e. flat tax increase), add increment to each
        elif ratio > 1:
            addition = ((ratio * increment) / len(newbrlist)) * (b + 1)
            newbrlist[b] =  round(newbrlist[b] + addition,4)
            #if your ration >1 (i.e. progressive tax increase), add increment
            #to lowest rate, then scale up to comply w/ ratio across brackets
    return newbrlist

"""
Function: determine effective tax rate for a person with a given AGI, status,
and at a specified year

Inputs:
    Year, an int
    Income, an int
    Status, a string (from FilingStatus list)
    BracketDict, a dictionary
    StandardDeduction, a dictionary
    Inflation, a dictionary

Output: effective tax rate, a float
"""

def effectiveincometax(Year,Income,Status,BracketDict,StandardDeduction,
                       Inflation):

    IncomeTaxesPaid = 0
    StandDeduc = StandardDeduction[Status]
    
    #create a list, depending on filing status, of tax rates and thresholds
    myfilingstatusbrlist = []
    for br in BracketDict[Status]:
        myfilingstatusbrlist.append([br,BracketDict[Status][br]])
    
    #adjust thresholds and standard deduction for inflation, from 2019 to specified year
    for y in range(Year-2019):
        for l in myfilingstatusbrlist:
            l[1] = l[1] * (1 + Inflation)
        StandDeduc = StandDeduc * (1 + Inflation)
    
    TaxableIncome = Income - StandDeduc
    
    #for each tax bracket, set the rate, threshold, and next threshold (0 if end of rates)
    for br in range(len(myfilingstatusbrlist)):
        rate = float(myfilingstatusbrlist[br][0])
        threshold = float(myfilingstatusbrlist[br][1])
        if br + 1 < len(myfilingstatusbrlist):
            nextthreshold = float(myfilingstatusbrlist[br+1][1])
        else:
            nextthreshold = 0

        if TaxableIncome >= threshold:
            if TaxableIncome < nextthreshold or nextthreshold == 0:
                IncomeTaxesPaid = IncomeTaxesPaid + (rate * (TaxableIncome - threshold))
                #if your taxable income >= threshold, but < next threshold (or
                #at the highest bracket already), multiply the current rate
                #by your taxable income minus the current threshold
            elif TaxableIncome >= nextthreshold:
                IncomeTaxesPaid = IncomeTaxesPaid + (rate * (nextthreshold - threshold))
                #if your taxable income >= threshold, and >= next threshold,
                #multiply the current rate by (nextthreshold - current threshold)
    
    if Income == 0:
        return 0
    
    else:
        return round(IncomeTaxesPaid/Income,4)
