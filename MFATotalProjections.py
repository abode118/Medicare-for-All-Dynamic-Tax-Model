"""
Created on Sat Sep 21 10:45:46 2019
@author: abode
"""

import string
import numpy
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
import matplotlib.ticker as ticker

import MFAvariables as m
import IncomeTaxes as i
import PayrollTaxes as p
import CorporateTaxes as c

"""
*******************************************************************************
HELPER FUNCTIONS (projection functions beginning ~line 300)
*******************************************************************************
"""

"""
*******************************************************************************
MARGINALTAXINCREASE()

Function: Determine marginal tax increases for a given status/income and increment
(i.e. payroll taxes have lower marginal impact on high earners due to caps)

Inputs:    
    OldBracketDict, a dictionary
    OldPayrollTaxList, a list
    ratio, an int
    increment, a float
    Year, an int
    Income, an int
    Status, a string
    Inflation, a float
    
Output: list of lists
    [[Income Tax, Incremental change in effective tax rate],
    [HI Tax, Incremental change in effective tax rate],
    [Addt'l HI Tax, Incremental change in effective tax rate]
    [Corp Tax, 0]]
*******************************************************************************
"""
def marginaltaxincrease(OldBracketDict,OldPayrollTaxList,
                        ratio,increment,Year,Income,Status,Inflation):
    
    newincomebrlist = i.raiseincometaxbrackets(OldBracketDict,ratio,increment)
    newbracketdict = i.newbracketdict(OldBracketDict,newincomebrlist)
    newHIpayrolltaxlist = p.raisepayrolltaxes(OldPayrollTaxList,increment*2,0)
    newaddtlHIpayrolltaxlist = p.raisepayrolltaxes(OldPayrollTaxList,0,increment)
    #calculate total effective tax rate given no changes
    nochange = totaleffectivetaxrate(OldBracketDict,OldPayrollTaxList,Year,Income,
                                     Status,Inflation)

    #calculate total effective tax rate given incremental change in income tax
    incometaxchangerate = totaleffectivetaxrate(newbracketdict,OldPayrollTaxList,
                                                Year,Income,Status,Inflation)
    
    #calculate total effective tax rate given incremental change in HI payroll tax
    HItaxchangerate = totaleffectivetaxrate(OldBracketDict,newHIpayrolltaxlist,Year,
                                            Income,Status,Inflation)
    
    #calculate total effective tax rate fiven incremental change in addt'l payroll tax
    addtlHItaxchangerate = totaleffectivetaxrate(OldBracketDict,newaddtlHIpayrolltaxlist,
                                                 Year,Income,Status,Inflation)
    
    #return list of lists, 
    return [['IncomeTax',round(incometaxchangerate - nochange,4)],
             ['HITax',round(HItaxchangerate - nochange,4)],
            ['AddtlHITax',round(addtlHItaxchangerate - nochange,4)],
            ['CorpTax',0]]

"""
*******************************************************************************
MARGINALREVENUEGAIN()

Function: Determine marginal gain in tax revenue for a given increment

Inputs:
        OldBracketDict, a dictionary
        OldCorpTaxRate, a float
        OldPayrollTaxList, a list
        StartYear, an int
        Years, an int
        Inflation, a float
        PopulationGrowth, a float
        GDPGrowth, a float
        ratio, an int
        increment, a float        
    
Output: list of lists
    [[Income Tax, Marginal change in tax revenue],
    [HI Tax, Marginal change in tax revenue],
    [Addt'l HI Tax, Marginal change in tax revenue]
    [Corp Tax, Marginal change in tax revenue]]
*******************************************************************************
"""
def marginalrevenuegain(OldBracketDict,OldCorpTaxRate,OldPayrollTaxList,
                        StartYear,Years,Inflation,PopulationGrowth,
                        GDPGrowth,ratio,increment):
    
    #generate new tax rates by raising each by increment
    newincomebrlist = i.raiseincometaxbrackets(OldBracketDict,ratio,increment)
    NewBracketDict = i.newbracketdict(OldBracketDict,newincomebrlist)
    newHIpayrolltaxlist = p.raisepayrolltaxes(OldPayrollTaxList,increment*2,0)
    newaddtlHIpayrolltaxlist = p.raisepayrolltaxes(OldPayrollTaxList,0,increment)
    NewCorpTaxRate = c.RaiseCorporateTax(OldCorpTaxRate,increment)
    
    #project tax revenue given one increment of change in each tax rate type    
    incometaxrevchange = compareprojections(OldBracketDict,NewBracketDict,
                                            OldCorpTaxRate,OldCorpTaxRate,
                                            OldPayrollTaxList,OldPayrollTaxList,
                                            StartYear,Years,Inflation,
                                            PopulationGrowth,GDPGrowth)

    HItaxrevchange = compareprojections(OldBracketDict,OldBracketDict,
                                        OldCorpTaxRate,OldCorpTaxRate,
                                        OldPayrollTaxList,newHIpayrolltaxlist,
                                        StartYear,Years,Inflation,
                                        PopulationGrowth,GDPGrowth)

    addtlHItaxrevchange = compareprojections(OldBracketDict,OldBracketDict,
                                             OldCorpTaxRate,OldCorpTaxRate,
                                             OldPayrollTaxList,newaddtlHIpayrolltaxlist,
                                            StartYear,Years,Inflation,
                                            PopulationGrowth,GDPGrowth)

    corptaxrevchange = compareprojections(OldBracketDict,OldBracketDict,
                                          OldCorpTaxRate,NewCorpTaxRate,
                                          OldPayrollTaxList,OldPayrollTaxList,
                                          StartYear,Years,Inflation,
                                          PopulationGrowth,GDPGrowth)
    
    return [['IncomeTax',incometaxrevchange[3]],['HITax',HItaxrevchange[3]],
            ['AddtlHITax',addtlHItaxrevchange[3]],['CorpTax',corptaxrevchange[3]]]

"""
*******************************************************************************
TOTALEFFECTIVETAXRATE()

Function: Determine total effective tax rate

Inputs:
    BracketDict, a dictionary
    PayrollTaxList, a list
    Year, an int
    Status, a String
    Inflation, a float
    
    Defaults:
        StandardDeduction, a dictionary

Output:
    total effective tax rate, a float
*******************************************************************************
"""
def totaleffectivetaxrate(BracketDict,PayrollTaxList,Year,Income,Status,Inflation,
                          StandardDeduction = m.StandardDeduction):
    incomet = i.effectiveincometax(Year,Income,Status,BracketDict,StandardDeduction,
                       Inflation)
    payrollt = p.effectivepayrolltax(Year,Income,Status,PayrollTaxList,Inflation)
    return incomet + payrollt

"""
*******************************************************************************
EFFECTIVERATECHANGESALL

Function: determining effective tax rate change for a person with a given AGI

Inputs:
    Year, an int
    OldBracketDict, a dictionary
    NewBracketDict, a dictionary
    Inflation, a float
    OldPayrollTaxList, a list
    NewPayrollTaxList, a list
    StandardDeduction, a dictionary (preset)
    FilingStatus, a list (preset)
    
Output: chart displaying effective change across 25k increments

Column 1 = Income
Column 2 = Filing Status
Column 3 = Effective Tax Rate
Column 4 = Rate or Change in Rate (Category)
*******************************************************************************
"""
def effectiveratechangesall(Year,OldBracketDict,NewBracketDict,
                            Inflation,OldPayrollTaxList,NewPayrollTaxList,
                            StandardDeduction = m.StandardDeduction,
                            FilingStatus = m.FilingStatus):
    
    for st in FilingStatus:
        result = []
        for income in range(0,525000,25000):
            originalincome = i.effectiveincometax(Year,income,st,OldBracketDict,
                                                StandardDeduction,Inflation)
            newincome = i.effectiveincometax(Year,income,st,NewBracketDict,
                                           StandardDeduction,Inflation)
            originalpayroll = p.effectivepayrolltax(Year,income,st,OldPayrollTaxList,
                                                  Inflation)
            newpayroll = p.effectivepayrolltax(Year,income,st,NewPayrollTaxList,
                                             Inflation)
            originaltotal = originalincome + originalpayroll
            newtotal = newincome + newpayroll
            
            result.append([int(income/1000),newtotal,"Effective Tax Rate"])
            result.append([int(income/1000),newtotal-originaltotal,"Effective Rate Change"])
        chartdata = pd.DataFrame(result,columns = ['Income',
                                                   'Rate',
                                                   'Effective Rate Cat'])
    
        plt.figure(figsize = (11,8.5))
        sns.set_palette("YlGnBu",4)
        fig = sns.barplot(x="Income",y="Rate",hue="Effective Rate Cat",data=chartdata,ci=None)
        fig.yaxis.set_major_locator(ticker.MultipleLocator(0.05))
        plt.ylim(0,0.55)
        yticklabels = ['{:.2%}'.format(y) for y in fig.get_yticks()]
        fig.set_yticklabels(yticklabels)
        fig.set(title = "New Effective Tax Rate and Change - " + str(st),
                xlabel = "Income (in thousands)",
                ylabel= "Effective Tax Rate")
        
    return None

"""
*******************************************************************************
VISUALIZATIONS

Chart 1: line chart depicting cumulative taxes raised with and without changes
Chart 2: line chart depicting cumulative change in taxes vs. desired coverage
Chart 3: bar chart depicting cumulative taxes raised in each cat with/without
         changes, and the difference
*******************************************************************************
"""
def taxrevlinechart(NoChangeArray,ChangeArray,StartYear,Years):
    
    ForGraph = []
    changesofar = 0
    nochangesofar = 0
    for yr in range(Years):
        nochangesofar += numpy.sum(NoChangeArray[yr])
        changesofar += numpy.sum(ChangeArray[yr])
        ForGraph.append([StartYear + yr, changesofar, "Tax Revenue Projections with Changes"])
        ForGraph.append([StartYear + yr, nochangesofar, "Current Tax Revenue Projections"])
    plt.figure(figsize = (11,8.5))
    TaxRevLineGraph = pd.DataFrame(ForGraph,columns = ['Year','Tax Revenue','Projection'])
    sns.set_palette("YlGnBu",2)
    fig = sns.lineplot(x="Year",y="Tax Revenue",hue="Projection",data=TaxRevLineGraph)
    yticklabels = ['{:,.2f}'.format(y) + 'T' for y in fig.get_yticks()/1000000000000]
    fig.set_yticklabels(yticklabels)
    fig.set(title = "Tax Revenue Collected With and Without Changes",
             xlabel = "Year",
             ylabel="Tax Revenue (in Trillions of Dollars)")
    
    return None

def newtaxrev(DiffArray,StartYear,Years,DesiredCoverage,TotalCost):
    
    ForGraph = []
    diffsofar = 0
    for yr in range(Years):
        diffsofar += numpy.sum(DiffArray[yr])
        ForGraph.append([StartYear + yr, DesiredCoverage * TotalCost,"Desired Coverage"])
        ForGraph.append([StartYear + yr, diffsofar, "Difference in Tax Revenue"])
    plt.figure(figsize = (11,8.5))
    TaxRevLineGraph = pd.DataFrame(ForGraph,columns = ['Year','Tax Revenue','Projection'])
    sns.set_palette("RdBu",2)
    fig = sns.lineplot(x="Year",y="Tax Revenue",hue="Projection",data=TaxRevLineGraph)
    yticklabels = ['{:,.2f}'.format(y) + 'T' for y in fig.get_yticks()/1000000000000]
    fig.set_yticklabels(yticklabels)
    fig.set(title = "Change in Tax Revenue vs. Desired Coverage",
             xlabel = "Year",
             ylabel="Tax Revenue (in Trillions of Dollars)")
    
    return None
        
def taxbarchart(barcharttotals):
    
    ForGraph2 = []
    revtypes = {"Income":4,"OASDI":0, "HI":1, "Addtl HI":2, "Corporate":3}
    projectdict = {"Current Tax Revenue Projections":0,"Tax Revenue Projections with Changes":1,
                   "Difference in TaxRevenue":2}
    for pr in projectdict.keys():
        for r in revtypes.keys():
            ForGraph2.append([barcharttotals[projectdict[pr]][revtypes[r]],r,pr])
    plt.figure(figsize = (11,8.5))
    TaxCatBarChart = pd.DataFrame(ForGraph2,columns = ['Revenue','Category','Projection'])
    sns.set_palette("YlGnBu",4)
    fig2 = sns.barplot(x="Category",y="Revenue",hue="Projection",data=TaxCatBarChart)
    yticklabels = ['{:,.2f}'.format(y) + 'T' for y in fig2.get_yticks()/1000000000000]
    fig2.set_yticklabels(yticklabels)
    fig2.set(title = "Tax Revenue by Category",
             xlabel = "Tax Category",
             ylabel="Tax Revenue (in Trillions of Dollars)")
    
    return None

"""
*******************************************************************************
TAX REVENUE PROJECTIONS
*******************************************************************************
"""

"""
*******************************************************************************
PROJECTTAXREVENUE()

Function: Project future tax revenues (income, payroll, corporate)

Inputs:
    BracketDict, a dictionary
    OldCorpTaxRate, a float
    NewCorpTaxRate, a float
    OldPayrollTaxList, a list
    NewPayrollTaxList, a list
    StartYear, an int
    Years, an int
    Inflation, a float
    PopulationGrowth, a float
    GDPGrowth, a float
        
    Default:
        IncomeTaxFile, a csv file
        StandardDeduction, a dictionary
        IncomeGroups, a dictionary
        FedRevFile, a csv file
        PayrollTaxFile, a csv file
        FilingStatus, a list
        BaseYearIP, an int (2016 latest for Income Tax Data/Payroll Tax)
        BaseYearC, an int (2018 latest for Corporate Tax Data)
        
Output: array of tax revenue for each tax category, for each year from
        StartYear to (StartYear + Years) - 1
        [OASDI Rev, Base HI Rev, Addt'l HI Rev, Corp Tax, Income Tax]
*******************************************************************************
"""
def projecttaxrevenue(BracketDict,OldCorpTaxRate,NewCorpTaxRate,
                      OldPayrollTaxList,NewPayrollTaxList,StartYear,Years,
                      Inflation,PopulationGrowth,GDPGrowth,
                      IncomeTaxFile = m.IncomeTaxData,
                      StandardDeduction = m.StandardDeduction,
                      IncomeGroups = m.IncomeGroups,
                      FedRevFile = m.FedRevData,
                      PayrollTaxFile = m.PayrollTaxData,
                      FilingStatus = m.FilingStatus,
                      BaseYearIP = 2016,
                      BaseYearC = 2018):
    #Generate arrays for each year of tax revenue projection
    PayrollTaxRev = p.ProjectPayrollTax(IncomeTaxFile,PayrollTaxFile,
                                          OldPayrollTaxList,NewPayrollTaxList,
                                          FilingStatus,IncomeGroups,BaseYearIP,
                                          StartYear,Years,Inflation,PopulationGrowth)
    CorpTaxRev = c.ProjectCorporateTax(FedRevFile,BaseYearC,StartYear,Years,
                                       OldCorpTaxRate,NewCorpTaxRate,
                                       Inflation,GDPGrowth)
    IncomeTaxRev = i.ProjectIncomeTax(IncomeTaxFile,BracketDict,StandardDeduction,
                                      IncomeGroups,BaseYearIP,StartYear,Years,Inflation,
                                      PopulationGrowth)
    
    #Aggregate arrays for each year of tax revenue projection
    TaxRev = []
    for yr in range(Years):
        TaxRev.append([PayrollTaxRev[yr][0],PayrollTaxRev[yr][1],PayrollTaxRev[yr][2],
                       CorpTaxRev[yr],IncomeTaxRev[yr]])        
    return numpy.array(TaxRev)

"""
*******************************************************************************
COMPAREPROJECTIONS()

Function: project future tax (income, payroll, corporate) with and without
          changes, and compare the difference

Inputs:
    OldBracketDict, a dictionary
    NewBracketDict, a dictionary
    OldCorpTaxRate, a float
    NewCorpTaxRate, a float
    OldPayrollTaxList, a list
    NewPayrollTaxList, a list
    StartYear, an int
    Years, an int
    Inflation, a float
    PopulationGrowth, a float
    GDPGrowth, a float
    
    Default:
        DesiredCoverage (set to 0 unless changed)
        TotalCost (set to 0 unless changed)
        Visualization (set to False unless changed)

Output:
    An array of the tax revenue for each category from StartYear to 
    (StartYear + Years) - 1    
    [[OASDI, HI, Addtl HI, Corp Tax, Income Tax] * Years -- projected w/ no changes,
    [[OASDI, HI, Addtl HI, Corp Tax, Income Tax] * Years -- projected w/ changes,
    [[OASDI, HI, Addtl HI, Corp Tax, Income Tax] * Years -- difference in each cat,
    TotalDiff -- total cumulativetax revenue difference]
    
    Plots four charts (see above) if Visualization == True
*******************************************************************************
"""
def compareprojections(OldBracketDict,NewBracketDict,
                       OldCorpTaxRate,NewCorpTaxRate,
                       OldPayrollTaxList,NewPayrollTaxList,
                       StartYear,Years,Inflation,PopulationGrowth,GDPGrowth,
                       DesiredCoverage = 0,
                       TotalCost = 0,
                       Visualization = False):
    
    #project tax revenue with no changes
    nochange = projecttaxrevenue(OldBracketDict,OldCorpTaxRate,OldCorpTaxRate,
                                 OldPayrollTaxList,OldPayrollTaxList,
                                 StartYear,Years,Inflation,PopulationGrowth,GDPGrowth)
  
    #project tax revenue with specified changes
    withchange = projecttaxrevenue(NewBracketDict,OldCorpTaxRate,NewCorpTaxRate,
                                   OldPayrollTaxList,NewPayrollTaxList,
                                   StartYear,Years,Inflation,PopulationGrowth,GDPGrowth)
    
    #calculate total rev collected per category, with and without rate changes 
    TaxCatTotals = [sum(x) for x in zip(*nochange)]
    ChangedTaxCatTotals = [sum(x) for x in zip(*withchange)]
    #calculate the difference per year per cat, total diff per year per cat, along with total diff
    DiffList = withchange - nochange
    DiffListTotals = [sum(x) for x in zip(*DiffList)]
    TotalDiff = numpy.sum(withchange) - numpy.sum(nochange)
    
    if Visualization == True:
        barcharttotals = [TaxCatTotals,ChangedTaxCatTotals,DiffListTotals]
        taxrevlinechart(nochange,withchange,StartYear,Years)
        newtaxrev(DiffList,StartYear,Years,DesiredCoverage,TotalCost)
        taxbarchart(barcharttotals)
        effectiveratechangesall(StartYear + Years,OldBracketDict,NewBracketDict,
                                Inflation,OldPayrollTaxList,NewPayrollTaxList)
    
    return [nochange,withchange,DiffList,TotalDiff]

#NewBracketDict = i.newbracketdict(i.BracketDict2019,[0.10,0.20,0.30,0.40,0.50,0.60,0.70])
#NewPayrollTaxList = p.newpayrolllist(p.PayrollTaxin19,[0.05,0.02])
#compareprojections(i.BracketDict2019,NewBracketDict,
#                   m.CurrentCorpTaxRate,0.325,
#                   p.PayrollTaxin19,NewPayrollTaxList,
#                   2020,10,m.Inflation,m.PopulationGrowth,m.GDPGrowth,
#                   DesiredCoverage = 0.25, TotalCost = 30000000000000,
#                   Visualization = True)

"""
*******************************************************************************
RAISEALLWCONSTRAINT()

Function: project future tax revenue, meeting constraints

Inputs:
    OldBracketDict, a dictionary (current brackets)
    ratio, an int (for progressive income tax brackets)
    OldCorpTaxRate, a float
    OldPayrollTaxList, a list
    StartYear, an int (Year you believe Medicare for All will start)
    Years, an int
    Inflation, a float
    PopulationGrowth, a float
    GDPGrowth, a float
    DesiredCoverage, a float
    TotalCost, an int
    startcovered, an int (0, unless used in final algorithm)
    
    Increments (to raise each tax rate per category; floats):
        incrementI, incrementC, incrementHI, incrementaddtl
    
    Constraints (maximum rates per category; floats):
        maxIncomeTax, maxHItax, maxaddtltax, maxcorptax
    
    Defaults:
        Visualization (True, unless changed)
        
Output:
    [[New Tax Bracket List],[New Payroll Tax Rates],New Corporate Tax Rate,
    Amount Covered by Function, Amount Covered pre Function, Total Amount Covered]
    
    Plots four charts (see above) if Visualization == True
*******************************************************************************
"""
def raiseallwconstraint(OldBracketDict,ratio,OldCorpTaxRate,OldPayrollTaxList,
                        StartYear,Years,Inflation,PopulationGrowth,GDPGrowth,
                        DesiredCoverage,TotalCost,startcovered,
                        incrementI,incrementC,incrementHI,incrementaddtl,
                        maxIncomeTax,maxHItax,maxaddtltax,maxcorptax,
                        Visualization = True):
    
    #initiate variables; amount covered from this function is zero,
    #Raise all rates (income brackets, payroll rates, corp tax rate) by their increments
    amtcovered = 0
    newbracketlist = i.raiseincometaxbrackets(OldBracketDict,ratio,incrementI)
    NewBracketDict = i.newbracketdict(OldBracketDict,newbracketlist)
    NewPayrollTaxList = p.raisepayrolltaxes(OldPayrollTaxList,incrementHI,incrementaddtl)
    NewCorpTaxRate = c.RaiseCorporateTax(OldCorpTaxRate,incrementC)

    #raise rates by respective increments until amt covered >= desired amt
    while (amtcovered + startcovered) < (DesiredCoverage * TotalCost):
        NoChange = 0
        
        #if current max tax bracket + increment is less than constraint, raise rates
        if round(max(newbracketlist) + (incrementI * ratio),4) > maxIncomeTax or incrementI == 0:
            NoChange += 1
        else:
            newbracketlist = i.raiseincometaxbrackets(NewBracketDict,ratio,incrementI)
            NewBracketDict = i.newbracketdict(OldBracketDict,newbracketlist)
        
        #if current payroll tax rates + increment are less than constraints,
        #raise rates
        if NewPayrollTaxList[2] + incrementHI > maxHItax or incrementHI == 0:
            NoChange += 1
        else:
            NewPayrollTaxList = p.raisepayrolltaxes(NewPayrollTaxList,incrementHI,0)
        if NewPayrollTaxList[3] + incrementaddtl > maxaddtltax or incrementaddtl == 0:
            NoChange += 1
        else:
            NewPayrollTaxList = p.raisepayrolltaxes(NewPayrollTaxList,0,incrementaddtl)
            
        #if corp tax rate + increment is less than constraint, raise rate
        if NewCorpTaxRate + incrementC > maxcorptax or incrementC == 0:
            NoChange += 1
        else:
            NewCorpTaxRate = c.RaiseCorporateTax(NewCorpTaxRate,incrementC)
        
        if NoChange == 4:
            break
        
        comparison = compareprojections(OldBracketDict,NewBracketDict,
                                        OldCorpTaxRate,NewCorpTaxRate,
                                        OldPayrollTaxList,NewPayrollTaxList,
                                        StartYear,Years,Inflation,PopulationGrowth,
                                        GDPGrowth,DesiredCoverage,TotalCost)
        amtcovered = comparison[3]
    
    if Visualization == True:
        compareprojections(OldBracketDict,NewBracketDict,OldCorpTaxRate,
                           NewCorpTaxRate,OldPayrollTaxList,NewPayrollTaxList,
                           StartYear,Years,Inflation,PopulationGrowth,GDPGrowth,
                           DesiredCoverage,TotalCost,Visualization = True)

        print('\n' + "Covered $"+ str('{:,}'.format(int(amtcovered + startcovered))) + "; " + \
              str(round((amtcovered + startcovered)/TotalCost * 100,2)) + \
              "% of the total cost ($" + str('{:,}'.format(TotalCost)) + \
              ") vs. goal of " + str(round(DesiredCoverage * 100,2)) + "%")
        print('\n' + 'New Income Brackets: ' + str(newbracketlist) + '\n' + \
              'New HI Payroll Tax Rates: ' + str(NewPayrollTaxList[2:4]) + '\n' + \
              'New Corporate Tax Rate: ' + str(NewCorpTaxRate) + '\n')
    
    return ([newbracketlist,NewPayrollTaxList[2:4],NewCorpTaxRate,
             round(amtcovered,2),startcovered,round(amtcovered+startcovered,2)])
    
#raiseallwconstraint(i.BracketDict2019,7,
#                    m.CurrentCorpTaxRate,
#                    p.PayrollTaxin19,
#                    2020,10,m.Inflation,m.PopulationGrowth,m.GDPGrowth,
#                    0.25,30000000000000,0,
#                    0.0025,0.0025,0.0025,0.0025,0.55,0.05,0.05,0.35)

"""
*******************************************************************************
RAISEALLFORAGIVENINCOME()

Function: Raise tax rates, meeting constraints, and choosing the option with 
the lowest impact for a person with a specified filing status and income

(i.e. determine marginal effective tax rate increase from raising each rate
by a certain increment)

Inputs:

    OldBracketDict, a dictionary
    OldCorpTaxRate, a float
    OldPayrollTaxList, a list
    StartYear, an int
    Years, an int
    Inflation, a float
    PopulationGrowth, a float
    GDPGrowth, a float
    ratio, an int
    increment, a float
    
    Constraints:
        Desired Coverage, a float
        Total Cost, an int
        startcovered, a float
        maxIncomeTax, a float
        maxHItax, a float
        maxaddtltax, a float
        maxcorptax, a float
        Income, an int
        Status, a string
    
Output: list
    [[Income Tax Brackets],HI Payroll Tax, HI addt'l Payroll Tax, Corporate Tax,
    amount covered by rate changes]
*******************************************************************************
"""
def raiseallforagivenincome(OldBracketDict,OldCorpTaxRate,OldPayrollTaxList,
                            StartYear,Years,Inflation,PopulationGrowth,GDPGrowth,
                            ratio,increment,DesiredCoverage,TotalCost,startcovered,
                            maxIncomeTax,maxHItax,maxaddtltax,maxcorptax,
                            Income,Status,Visualization = True):
    
    margrate = marginaltaxincrease(OldBracketDict,OldPayrollTaxList,ratio,
                                   increment,StartYear + Years,Income,Status,Inflation)
        
    covered = 0
    margrate.sort(key = lambda x: x[1])
    for t in margrate:
        if t[0] == 'IncomeTax':
            if covered >= DesiredCoverage * TotalCost:
                increment = 0
            incometaxchange = raiseallwconstraint(OldBracketDict,ratio,OldCorpTaxRate,
                                                  OldPayrollTaxList,StartYear,Years,Inflation,
                                                  PopulationGrowth,GDPGrowth,
                                                  DesiredCoverage,TotalCost,covered,
                                                  increment,0,0,0,
                                                  maxIncomeTax,maxHItax,maxaddtltax,maxcorptax,
                                                  Visualization = False)
            covered += incometaxchange[3]
            
        elif t[0] == 'CorpTax':
            if covered >= DesiredCoverage * TotalCost:
                increment = 0
            corptaxchange = raiseallwconstraint(OldBracketDict,ratio,OldCorpTaxRate,
                                                OldPayrollTaxList,StartYear,Years,Inflation,
                                                PopulationGrowth,GDPGrowth,
                                                DesiredCoverage,TotalCost,covered,
                                                0,increment,0,0,
                                                maxIncomeTax,maxHItax,maxaddtltax,maxcorptax,
                                                Visualization = False)
            covered += corptaxchange[3]
            
        elif t[0] == 'HITax':
            if covered >= DesiredCoverage * TotalCost:
                increment = 0
            HItaxchange = raiseallwconstraint(OldBracketDict,ratio,OldCorpTaxRate,
                                              OldPayrollTaxList,StartYear,Years,Inflation,
                                              PopulationGrowth,GDPGrowth,
                                              DesiredCoverage,TotalCost,covered,
                                              0,0,increment,0,
                                              maxIncomeTax,maxHItax,maxaddtltax,maxcorptax,
                                              Visualization = False)
            covered += HItaxchange[3]
            
        elif t[0] == 'AddtlHITax':
            if covered >= DesiredCoverage * TotalCost:
                increment = 0
            addtlHItaxchange = raiseallwconstraint(OldBracketDict,ratio,OldCorpTaxRate,
                                                   OldPayrollTaxList,StartYear,Years,Inflation,
                                                   PopulationGrowth,GDPGrowth,
                                                   DesiredCoverage,TotalCost,covered,
                                                   0,0,0,increment,
                                                   maxIncomeTax,maxHItax,maxaddtltax,maxcorptax,
                                                   Visualization = False)
            covered += addtlHItaxchange[3]

    if Visualization == True:
        NewBracketDict = i.newbracketdict(OldBracketDict,incometaxchange[0])
        NewPayrollTaxList = p.newpayrolllist(OldPayrollTaxList,[HItaxchange[1][0],addtlHItaxchange[1][1]])
        compareprojections(OldBracketDict,NewBracketDict,
                           OldCorpTaxRate,corptaxchange[2],
                           OldPayrollTaxList,NewPayrollTaxList,
                           StartYear,Years,Inflation,PopulationGrowth,
                           GDPGrowth,DesiredCoverage,TotalCost,Visualization = True)    
        
        print('\n' + "Covered $"+ str('{:,}'.format(int(covered + startcovered))) + "; " + \
              str(round((covered + startcovered)/TotalCost * 100,2)) + \
              "% of the total cost ($" + str('{:,}'.format(TotalCost)) + \
              ") vs. goal of " + str(round(DesiredCoverage * 100,2)) + "%")
        
        print('\n' + 'New Income Brackets: ' + str(incometaxchange[0]) + '\n' + \
              'New HI Payroll Tax Rates: ' + str(NewPayrollTaxList[2:4]) + '\n' + \
              'New Corporate Tax Rate: ' + str(corptaxchange[2]) + '\n')
        
    return [incometaxchange[0],HItaxchange[1][0],addtlHItaxchange[1][1],corptaxchange[2],covered]

#raiseallforagivenincome(i.BracketDict2019,m.CurrentCorpTaxRate,p.PayrollTaxin19,
#                        2021,10,0.02,0.01,0.02,2,0.001,0.50,30000000000000,
#                        0,0.55,0.05,0.05,0.30,100000,"Married filed jointly + Surviving Spouses")
"""
*******************************************************************************
PLUGANDPLAY()

Function: DIY plug and play new tax rates and assumptions

Inputs:
    Defaults:
        OldBracketDict, a dictionary
        OldCorpTaxRate, a float
        OldPayrollTaxList, a list

Output: total covered, a float
*******************************************************************************
"""
def plugandplay(OldBracketDict = i.BracketDict2019,OldCorpTaxRate = m.CurrentCorpTaxRate,
                OldPayrollTaxList = p.PayrollTaxin19):
    
    CurrBrackets = []
    for key in OldBracketDict.keys():
        for br in OldBracketDict[key].keys():
            if float(br) * 100 not in CurrBrackets:
                CurrBrackets.append(round(float(br) * 100,2))
    
    print("\n" + "***************************" + "\n" + "Current Income Tax Brackets are " + str(CurrBrackets))
    while True:
        NewBracketList = input("Please list 7 new income tax rates, in format: 10.00,20.00 etc: ")
        temp = []
        currentnum = ""        
        for n in NewBracketList:
            if n == "." or n in string.digits:
                currentnum = currentnum + n
            elif n == ',':
                temp.append(round(float(currentnum)/100,4))
                currentnum = ""
        temp.append(round(float(currentnum)/100,4))
        if len(temp) == 7:
            break    
    NewBracketDict = i.newbracketdict(OldBracketDict,temp)
    
    print("\n" + "***************************" + "\n" + 
          "Current HI Payroll Tax Rates are: Base Rate: " + str(round(OldPayrollTaxList[2] * 100/2,2)) + \
          "; Addt'l Rate (Income > $200,000): " + str(round(OldPayrollTaxList[3] * 100,2)))
    while True:
        NewPayrollTaxes = input("Please list your base and additional HI (Medicare) tax rates, in format: 1.00,2.00: ")
        temp = []
        currentnum = ""        
        for n in NewPayrollTaxes:
            if n == "." or n in string.digits:
                currentnum = currentnum + n
            elif n == ',':
                temp.append(round(float(currentnum)/100,4))
                currentnum = ""
        temp.append(round(float(currentnum)/100,4))
        if len(temp) == 2:
            break
    temp[0] = temp[0] * 2
    NewPayrollTaxList = p.newpayrolllist(OldPayrollTaxList,temp)
    
    print("\n" + "***************************" + "\n" + "CurrentCorporate Tax Rate is " + str(OldCorpTaxRate * 100))
    NewCorpTaxRate = input("Please list your new Corporate Tax Rate, in format: 1.00: ")
    currentnum = ""        
    for n in NewCorpTaxRate:
        if n == "." or n in string.digits:
            currentnum = currentnum + n
    NewCorpTaxRate = round(float(currentnum)/100,4)
            
    StartYear = int(input("Please choose a starting year (beyond 2019), in format 2020: "))
    
    Years = int(input("Please choose number of years to project revenue, in format 10: "))
    
    TotalCost = input("Please choose a total cost over years specified, in format 10000000: ")
    TotalCost = int(TotalCost.replace(',',''))
    
    InflationEst = input("Please choose an estimated Inflation Rate, in format: 1.00: ")
    currentnum = ""        
    for n in InflationEst:
        if n == "." or n in string.digits:
            currentnum = currentnum + n
    InflationEst = round(float(currentnum)/100,4)
    
    PopulationGrowthEst = input("Please choose an estimated Population Growth Rate, in format: 1.00: ")
    currentnum = ""        
    for n in PopulationGrowthEst:
        if n == "." or n in string.digits:
            currentnum = currentnum + n
    PopulationGrowthEst = round(float(currentnum)/100,4)
    
    GDPGrowthEst = input("Please choose an estimated GDP Growth Rate, in format: 1.00: ")
    currentnum = ""        
    for n in GDPGrowthEst:
        if n == "." or n in string.digits:
            currentnum = currentnum + n
    GDPGrowthEst = round(float(currentnum)/100,4)
    
    DesiredCoverage = input("Please choose a Desired Coverage Rate, in format: 1.00: ")
    currentnum = ""        
    for n in DesiredCoverage:
        if n == "." or n in string.digits:
            currentnum = currentnum + n
    DesiredCoverage = round(float(currentnum)/100,4)
    
    covered = compareprojections(OldBracketDict,NewBracketDict,
                                 OldCorpTaxRate,NewCorpTaxRate,
                                 OldPayrollTaxList,NewPayrollTaxList,
                                 StartYear,Years,InflationEst,PopulationGrowthEst,
                                 GDPGrowthEst,DesiredCoverage,TotalCost,
                                 Visualization = True)
    
    print("\n" + \
          "You were able to cover $"+str('{:,}'.format(covered[3]))+";" + "\n" + \
          "this is " + str(round(covered[3]/TotalCost*100,4)) + "%, vs. your goal of " + str(DesiredCoverage*100) + "%" \
          + "\n")
    
    return covered[3]
    
#plugandplay()
