#from MachineLearningAlgo.mltools import *
#from MachineLearningAlgo.mtools_2 import *
import csv as csv

import numpy as np

from temp.MachineLearningAlgo.mltoolsLNKD import *

'''
# Get Data

date, bid, ask = np.loadtxt('/Users/AlvinMbabazi/PycharmProjects/PyChit/MachineLearningAlgo/GBPUSD1d.txt', unpack=True,
                            delimiter=',',  # What Separates Each Value
                            # Converts the '0:' O width elements, to dates.
                            converters={0: mdates.strpdate2num('%Y%m%d%H%M%S')})



#graphRawFX()


totalStart = time.time()
Run(date, bid, ask)
totalEnd = time.time()-totalStart

print '_________________________________________________________'

print 'Pattern storing took:', endTime - startTime
print 'Entire processing took:',totalEnd,'seconds'
'''

date, bid, ask = np.loadtxt('/Users/Alvin/PycharmProjects/PyChit/MachineLearningAlgo/GBPUSD1d.txt', unpack=True,
                            delimiter=',',  # What Separates Each Value
                            # Converts the '0:' O width elements, to dates.
                            converters={0: mdates.strpdate2num('%Y%m%d%H%M%S')})

# LinkedIn Study
#'''
# Get Data

csv_file_object = csv.reader(open('/Users/Alvin/Desktop/LNKD_Data.csv', 'rb'))
header = csv_file_object.next()       # The next() command just skips the first line which is a header

data = []                             # Create a variable called 'data'.
for row in csv_file_object:           # Run through each row in the csv file,
    data.append(row)                  # adding each row to the data variable
data = np.array(data)

date = data[:, 0]
pricetemp = data[:, 1]
#price = []
price = ((bid + ask) / 2)
#for each in pricetemp:
 #   price.append(float(each))

print 'Dates:', date
print 'Prices:', price

#graphRawFX()

totalStart = time.time()
#Run(date, price)
Run(date, price)
totalEnd = time.time()-totalStart

print '_________________________________________________________'

print 'Entire processing took:',totalEnd,'seconds'
#'''
