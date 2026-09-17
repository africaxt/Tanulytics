import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
import numpy as np

import time

tStart = time.time()

# Function for Calculating Percent Change
def percentChange(startPoint, currentPoint):
    try:
        x = ((float(currentPoint)-startPoint)/abs(startPoint))*100.00
        if x == 0.0:
            return 0.00000000000001
        else:
            return x
    except:
        return 0.00000000000001

# Function for doing this for all values of data.
def patternStorage(avgLine, patternAr, performanceAr):
    '''
    The goal of patternFinder is to begin collection of %change patterns
    in the tick data. From there, we also collect the short-term outcome
    of this pattern. Later on, the length of the pattern, how far out we
    look to compare to, and the length of the compared range be changed,
    and even THAT can be machine learned to find the best of all 3 by
    comparing success rates.
    '''

  # This finds the length of the total array for us
    x = len(avgLine) - 60
    # This will be our starting point, allowing us to compare to the
    # past 10 % changes.
    y = 31
    # where we are in a trade. #
    # can be none, buy,
    currentStance = 'none'

    while y < x:
        pattern = []
        for n in range(29, -1, -1):
            pattern.append(percentChange(avgLine[y-30], avgLine[y-n]))  # Essentially First to 10th Elements

        outcomeRange = avgLine[y+20:y+30]  # We are averaging the outcome of 20-30 points in the future.
        currentPoint = avgLine[y]

        # Function to account for the average of the items in the array
        try:
            avgOutcome = reduce(lambda x, y: x + y, outcomeRange) / len(outcomeRange)
        except Exception, e:
            print str(e)
            avgOutcome = 0

        futureOutcome = percentChange(currentPoint, avgOutcome)

        patternAr.append(pattern)
        performanceAr.append(futureOutcome)

        y += 1


def currentPattern(avgLine, patForRec):

    for n in range(-30, 0, 1):
        patForRec.append(percentChange(avgLine[-31], avgLine[n]))  # Essentially Last to n+1 th = 10th to last Element


def patternRecognition(allData, toWhat, patternAr, performanceAr, patForRec, accuracyArray):
    predictedOutcomesAr = []
    patFound = 0
    plotPatAr = []

    for eachPattern in patternAr:
        # We will tell how similar things are by doing a percentage change...
        # if the % change (difference) is 1-2%, they are 98-99% similar.
        simTotal = 0
        for n in range(0, 30, 1):
            simTotal += (100.00 - abs(percentChange(eachPattern[n], patForRec[n])))

        howSim = (simTotal)/30.00

        if howSim > 75:     # We only want patterns that are greater than 70
            patdex = patternAr.index(eachPattern)   # Find this index number of the current pattern

            patFound = 1


            print '##################################'
            print '##################################'
            print '##################################'
            print '##################################'
            print patForRec
            print '==================================='
            print '==================================='
            print eachPattern
            print '----------'
            print 'Match:', howSim
            print 'Predicted Outcome:', performanceAr[patdex]   # Historical Performance of this pattern

            xp = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]

            plotPatAr.append(eachPattern)

            print '##################################'
            print '##################################'
            print '##################################'
            print '##################################'

    predArray = []

    if patFound == 1:
            fig = plt.figure(figsize=(10, 6))

            for eachPat in plotPatAr:
                futurePoints = patternAr.index(eachPat)

                if performanceAr[futurePoints] > patForRec[29]:
                    pcolor = '#24bc00'
                    predArray.append(1.000)
                else:
                    pcolor = '#d40000'
                    predArray.append(-1.000)

                plt.plot(xp, eachPat)
                plt.scatter(35, performanceAr[futurePoints], c=pcolor, alpha=.3)
                predictedOutcomesAr.append(performanceAr[futurePoints])

            realOutcomeRange = allData[toWhat + 20:toWhat + 30]
            realAvgOutcome = reduce(lambda x, y: x + y, realOutcomeRange) / len(realOutcomeRange)
            realFutureOutcome = percentChange(allData[toWhat], realAvgOutcome)

            predictedAvgOutcome = reduce(lambda x, y: x + y, predictedOutcomesAr) / len(predictedOutcomesAr)

            plt.scatter(40, realFutureOutcome, c='#54fff7', s=25)
            plt.scatter(40, predictedAvgOutcome, c='b', s=25)

            plt.plot(xp, patForRec, '#54fff7', linewidth=3)
            plt.grid(True)
            plt.title('Pattern Recognition')
            plt.show()

            print predArray

            predictionAverage = reduce(lambda x, y: x + y, predArray) / len(predArray)

            print predictionAverage
            print predictedAvgOutcome

     #       if predictionAverage < 0:
      #          print 'drop prediction'
      #          print patForRec[29]
      #          print realFutureOutcome
      #          if realFutureOutcome < patForRec[29]:
      #              accuracyArray.append(100)
      #          else:
      #              accuracyArray.append(0)

      #      if predictionAverage > 0:
      #          print 'rise prediction'
      #          print patForRec[29]
      #          print realFutureOutcome
      #          if realFutureOutcome > patForRec[29]:
      #              accuracyArray.append(100)
      #          else:
      #              accuracyArray.append(0)

      #      return accuracyArray



tEnd = time.time() - tStart
print 'Loading Time:',tEnd,'seconds'



def Run(date, bid, ask):

    dataLength = int(bid.shape[0])

    print 'data length is', dataLength

    toWhat = 37000  # From beginning of data - to what point are we going to consider

    allData = ((bid + ask) / 2)

    # BACKTESTER

    accuracyArray = []
    samps = 0

    while toWhat < dataLength:

        avgLine = allData[:toWhat]  # This specific program will always have data from day 1.
        # Global Variables
        patternAr = []
        performanceAr = []
        patForRec = []

        startTime = time.time()
        patternStorage(avgLine, patternAr, performanceAr)  # Historical Patterns
        endTime = time.time()

        # print len(patternAr)
        # print len(performanceAr)

        currentPattern(avgLine, patForRec)  # Current Pattern

        patternRecognition(allData, toWhat, patternAr, performanceAr, patForRec, accuracyArray)
        #moveOn = raw_input('Press Enter to Continue...')


        samps += 1
        toWhat += 1

        #print accuracyArray
        #accuracyAverage = reduce(lambda x, y: x + y, accuracyArray) / len(accuracyArray)
        #print 'Backtested Accuracy is', str(accuracyAverage) + '% after', samps, 'actionable trades'




