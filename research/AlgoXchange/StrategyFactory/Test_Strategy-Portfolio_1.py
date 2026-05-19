"""Test Strategy Portfolio is essentially to test the functionality of
    integrating my portfolio analysis and record keeping into python"""

# Machine Learning Based of Udacity 'Machine Learning for Trading Course'

# STRATEGY
#
# Buy and Hold Strategy
# - Later Input: When i bought, and when i sold.


# Algorithm functionality
#
# - Daily Portfolio Value
# - Portfolio Statistics

import sys
from Chit.Connect.GettingData.CSV_PyChit import *
from Chit.Connect.GettingData.IntraDay_Google import *
from Chit.config.PyChitStaX import *

base_dir = "/Users/Alvin/Cloud HDD/Dropbox (PWM Tech)/PWM Tech Team Folder/TraderChit/Test_Strategy-Portfolio_1/"

startDate = "2010-01-01"
endDate = "2016-09-10"

dates = pd.date_range(startDate, endDate)
symbols = ['TSLA', 'HCP']

data = get_data(symbols, dates, base_dir)

dateCheck = 0
if data.index[-1] != pd.to_datetime(endDate):
    while dateCheck == 0:
        print 'Given "end" date:', pd.to_datetime(endDate)
        print 'Last date in data:', data.index[-1]
        print '--------------------'
        print data.index[-1] - pd.to_datetime(endDate)
        print '--------------------'
        kill = raw_input('The last date in the data does NOT match your given end date. End program...? [y/n]: ')
        print ''
        if kill == 'y':
            sys.exit()
        else:
            if kill == 'n':
                dateCheck = 1


print endDate
print data.index[-1] != pd.to_datetime(endDate)
print data.index[-1] == pd.to_datetime(endDate)
print (pd.to_datetime(endDate) - pd.to_datetime(endDate)) == pd.to_datetime(0)


# Fill in Missing Data
data.ffill(inplace=True)
data.bfill(inplace=True)

#plot_data(data)
#plot_selected(data, symbols, "2010-01-01", "2016-09-10")

print data

# Create Strategy Portfolio
normed = normalize_data(data)
allocs = [0, 0.1, 0.9]
alloced = normed*allocs

pos_val = alloced*1000000   # Starting Value

port_vals = pos_val.sum(axis=1)

print port_vals

# Plotting function in mtools.py is not working
#plot_data(port_vals, "Equity Curve")

port_stats = stax(port_vals)
print port_stats

#save_data(port_stats, "portfolioBalanceSheet", base_dir)
