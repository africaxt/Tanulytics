'''MachineLearning_1.0 is the first version of Chit's machine algorithmic trading systems'''

# Basis of This Trading System:
# 1. Determine Pattern Length
# 2. Determine Pattern Collection Instructions to IDENTIFY
# 3. Get/Collect Patterns from Data
# 4. Use Pattern Recognition to LearnAI and PREDICT the likely outcome of current pattern
# 5. Backtest the variables used (data length, learning pit size, etc) throughout the dataset to DECIDE if its viable
# 6. Show Performance & Statistics


from Chit.Connect.GettingData.IntraDay_Google import get_google_data
from Chit.LearnAI.PyChitPatternRecognition import *
from Chit.LearnAI.PyChitPatterns import *
import time

rawdata = get_google_data("TSLA", 3600, 20000)
data = rawdata.values[:, 0]


# 1. Pattern size/length variable aka "The Magic Variable"
#some skeleton code below (commented out)
"""
if(parameters necessary to work out magic variable existent):
	z = func_that_works_out_magic_variable()
else:
	z = 30 # <-- Your default variable

Note: func_that_works_out_magic_variable() must include optimization capabilities. It has not yet been created
"""
# TODO - Key Var 1 - The Magic Variable Optimization
z = 30  # The magic variable: The amount of data captured by each pattern (Pattern Length/Size Variable)
# Default = 30

# 2. Pattern Collection Instructions
#   Default = percent change from first point to each point in the range.
#   Alt = log scaling
#   % Change of cumulative product

# Essentially any why to quantitatively sensationalize data with patterns.

# 3. Get Patterns
"""
tstart = time.time()
patternAr, performanceAr = getpatterns(data, z)     # Instruction file from step 2 will go into this function.
tend = time.time() - tstart
print '~/Chit$: "Pattern Extraction Complete"'
print 'Processing Time:', tend, 'seconds'
print '____________________________________\n'
print ''
print 'Patterns:'
print ''
print patternAr
print ''
print ''
print 'Outcomes: T + 20-30'
print ''
print performanceAr
print ''
"""

# 4. Machine Learning Patterns (The Strategy)  # TODO - Chit-M-Learning Strategy Factory Zone
# From allData we need to pick the end of out in-sample data, & starting point of our out of sample data.

# In - Sample Data: From beginning of data...
toWhat = int(len(data)*.50)

accuracyArray = []
samps = 0


# BACKTESTER - rolling forward cross validation

while toWhat < len(data):

    extract = data[:toWhat]     # This specific program will always have data from day 1.

    patForRec = []

    tstart = time.time()
    patternAr, performanceAr = getpatterns(extract, z)     # Instruction file from step 2 will go into this function.
    tend = time.time() - tstart
    print 'Processing Time:', tend, 'seconds'
    print ''
    print ''

    currentPattern(extract, patForRec)  # Current Pattern

    PatRec(patForRec, patternAr, performanceAr, accuracyArray, data, toWhat)
    # Test Predictions


    #patternRecognition(allData, toWhat, patternAr[:(toWhat - 32)], performanceAr[:(toWhat - 32)], patForRec, accuracyarray)

    # moveOn = raw_input('Press Enter to Continue...')

    toWhat += 1
    samps += 1

print "End"

print ' '
print 'Accuracy Array:', accuracyArray
accuracyAverage = reduce(lambda x, y: x + y, accuracyArray) / len(accuracyArray)
print 'Backtested Accuracy is', str(accuracyAverage) + '% after', samps, 'actionable trades'





# 5. Backtest / Performance Simulation - works hand in hand with the machine learner - "strategy" for the backtest.
# TODO Make the backtester a universal thing to test even non machine learning stategies

# 6. Realistic Trade Simulation


