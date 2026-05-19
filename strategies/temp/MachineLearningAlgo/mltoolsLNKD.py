import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
import numpy as np
import sys

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
    x = len(avgLine) - 32
    # This will be our starting point, allowing us to compare to the
    # past 30 % changes.
    y = 31
    # where we are in a trade. #
    # can be none, buy,
    currentStance = 'none'

    while y < x:
        pattern = []
        p1 = percentChange(avgLine[y-30], avgLine[y-29])  # Essentially First to 10th Elements
        p2 = percentChange(avgLine[y-30], avgLine[y-28])
        p3 = percentChange(avgLine[y-30], avgLine[y-27])
        p4 = percentChange(avgLine[y-30], avgLine[y-26])
        p5 = percentChange(avgLine[y-30], avgLine[y-25])
        p6 = percentChange(avgLine[y-30], avgLine[y-24])
        p7 = percentChange(avgLine[y-30], avgLine[y-23])
        p8 = percentChange(avgLine[y-30], avgLine[y-22])
        p9 = percentChange(avgLine[y-30], avgLine[y-21])
        p10 = percentChange(avgLine[y-30], avgLine[y-20])

        p11 = percentChange(avgLine[y-30], avgLine[y-19])
        p12 = percentChange(avgLine[y-30], avgLine[y-18])
        p13 = percentChange(avgLine[y-30], avgLine[y-17])
        p14 = percentChange(avgLine[y-30], avgLine[y-16])
        p15 = percentChange(avgLine[y-30], avgLine[y-15])
        p16 = percentChange(avgLine[y-30], avgLine[y-14])
        p17 = percentChange(avgLine[y-30], avgLine[y-13])
        p18 = percentChange(avgLine[y-30], avgLine[y-12])
        p19 = percentChange(avgLine[y-30], avgLine[y-11])
        p20= percentChange(avgLine[y-30], avgLine[y-10])

        p21 = percentChange(avgLine[y-30], avgLine[y-9])
        p22 = percentChange(avgLine[y-30], avgLine[y-8])
        p23 = percentChange(avgLine[y-30], avgLine[y-7])
        p24 = percentChange(avgLine[y-30], avgLine[y-6])
        p25 = percentChange(avgLine[y-30], avgLine[y-5])
        p26 = percentChange(avgLine[y-30], avgLine[y-4])
        p27 = percentChange(avgLine[y-30], avgLine[y-3])
        p28 = percentChange(avgLine[y-30], avgLine[y-2])
        p29 = percentChange(avgLine[y-30], avgLine[y-1])
        p30 = percentChange(avgLine[y-30], avgLine[y])

        outcomeRange = avgLine[y+20:y+30]  # We are averaging the outcome of 20-30 points in the future.
        currentPoint = avgLine[y]

        # Function to account for the average of the items in the array
        try:
            avgOutcome = reduce(lambda x, y: x + y, outcomeRange) / len(outcomeRange)
        except Exception, e:
            print str(e)
            avgOutcome = 0

        futureOutcome = percentChange(currentPoint, avgOutcome)


        # Print some logics
        '''
        print 'where we are historically:',currentPoint
        print 'soft outcome of the horizon:',avgOutcome
        print 'This pattern brings a future change of:',futureOutcome
        print '_______'
        print p1, p2, p3, p4, p5, p6, p7, p8, p9, p10
        '''
        #print p1, p2, p3, p4, p5, p6, p7, p8, p9, p10
        #moveOn = raw_input('Press Enter to Continue...')

        pattern.append(p1)
        pattern.append(p2)
        pattern.append(p3)
        pattern.append(p4)
        pattern.append(p5)
        pattern.append(p6)
        pattern.append(p7)
        pattern.append(p8)
        pattern.append(p9)
        pattern.append(p10)

        pattern.append(p11)
        pattern.append(p12)
        pattern.append(p13)
        pattern.append(p14)
        pattern.append(p15)
        pattern.append(p16)
        pattern.append(p17)
        pattern.append(p18)
        pattern.append(p19)
        pattern.append(p20)

        pattern.append(p21)
        pattern.append(p22)
        pattern.append(p23)
        pattern.append(p24)
        pattern.append(p25)
        pattern.append(p26)
        pattern.append(p27)
        pattern.append(p28)
        pattern.append(p29)
        pattern.append(p30)

        # can use .index to find the index value, then search for that value to get the matching information.
        # so like, performanceAr.index(12341)
        patternAr.append(pattern)
        performanceAr.append(futureOutcome)

        y += 1


def currentPattern(avgLine, patForRec):

    cp1 = percentChange(avgLine[-31], avgLine[-30])  # Essentially Last to n+1 th = 10th to last Element
    cp2 = percentChange(avgLine[-31], avgLine[-29])
    cp3 = percentChange(avgLine[-31], avgLine[-28])
    cp4 = percentChange(avgLine[-31], avgLine[-27])
    cp5 = percentChange(avgLine[-31], avgLine[-26])
    cp6 = percentChange(avgLine[-31], avgLine[-25])
    cp7 = percentChange(avgLine[-31], avgLine[-24])
    cp8 = percentChange(avgLine[-31], avgLine[-23])
    cp9 = percentChange(avgLine[-31], avgLine[-22])
    cp10 = percentChange(avgLine[-31], avgLine[-21])

    cp11 = percentChange(avgLine[-31], avgLine[-20])
    cp12 = percentChange(avgLine[-31], avgLine[-19])
    cp13 = percentChange(avgLine[-31], avgLine[-18])
    cp14 = percentChange(avgLine[-31], avgLine[-17])
    cp15 = percentChange(avgLine[-31], avgLine[-16])
    cp16 = percentChange(avgLine[-31], avgLine[-15])
    cp17 = percentChange(avgLine[-31], avgLine[-14])
    cp18 = percentChange(avgLine[-31], avgLine[-13])
    cp19 = percentChange(avgLine[-31], avgLine[-12])
    cp20 = percentChange(avgLine[-31], avgLine[-11])

    cp21 = percentChange(avgLine[-31], avgLine[-10])
    cp22 = percentChange(avgLine[-31], avgLine[-9])
    cp23 = percentChange(avgLine[-31], avgLine[-8])
    cp24 = percentChange(avgLine[-31], avgLine[-7])
    cp25 = percentChange(avgLine[-31], avgLine[-6])
    cp26 = percentChange(avgLine[-31], avgLine[-5])
    cp27 = percentChange(avgLine[-31], avgLine[-4])
    cp28 = percentChange(avgLine[-31], avgLine[-3])
    cp29 = percentChange(avgLine[-31], avgLine[-2])
    cp30 = percentChange(avgLine[-31], avgLine[-1])

    patForRec.append(cp1)
    patForRec.append(cp2)
    patForRec.append(cp3)
    patForRec.append(cp4)
    patForRec.append(cp5)
    patForRec.append(cp6)
    patForRec.append(cp7)
    patForRec.append(cp8)
    patForRec.append(cp9)
    patForRec.append(cp10)

    patForRec.append(cp11)
    patForRec.append(cp12)
    patForRec.append(cp13)
    patForRec.append(cp14)
    patForRec.append(cp15)
    patForRec.append(cp16)
    patForRec.append(cp17)
    patForRec.append(cp18)
    patForRec.append(cp19)
    patForRec.append(cp20)

    patForRec.append(cp21)
    patForRec.append(cp22)
    patForRec.append(cp23)
    patForRec.append(cp24)
    patForRec.append(cp25)
    patForRec.append(cp26)
    patForRec.append(cp27)
    patForRec.append(cp28)
    patForRec.append(cp29)
    patForRec.append(cp30)

    # print patForRec



# TODO Cut 99% of processing time that is from this function
# Numpy Array - 'blist' Import
# Jython
# CPython - Write it in C and create a python import for it. (C does parallel programming)
# Threading on Python
# NVIDIA CUDA
# Icrease time frame

def patternRecognition(allData, toWhat, patternAr, performanceAr, patForRec, accuracyArray):
    predictedOutcomesAr = []
    patFound = 0
    plotPatAr = []

    # TODO Machine Learning Basics:
    # Play with these variables and as long as performance is accelerating marginally,
    # you continue manipulating that variable, until this is no longer the case.

    for eachPattern in patternAr:
        # We will tell how similar things are by doing a percentage change...
        # if the % change (difference) is 1-2%, they are 98-99% similar.

        simreq = 60.00  # Each comparison point must be 50% similar
        patsimreq = 0.00  # We only want patterns that are greater than 60

        # First Pattern Recognition Algorithm: % Change from start point to each point
        #'''
        sim1 = 100.00 - abs(percentChange(eachPattern[0], patForRec[0]))
        sim2 = 100.00 - abs(percentChange(eachPattern[1], patForRec[1]))
        sim3 = 100.00 - abs(percentChange(eachPattern[2], patForRec[2]))
        sim4 = 100.00 - abs(percentChange(eachPattern[3], patForRec[3]))
        sim5 = 100.00 - abs(percentChange(eachPattern[4], patForRec[4]))
        sim6 = 100.00 - abs(percentChange(eachPattern[5], patForRec[5]))
        sim7 = 100.00 - abs(percentChange(eachPattern[6], patForRec[6]))
        sim8 = 100.00 - abs(percentChange(eachPattern[7], patForRec[7]))
        sim9 = 100.00 - abs(percentChange(eachPattern[8], patForRec[8]))
        sim10 = 100.00 - abs(percentChange(eachPattern[9], patForRec[9]))

        sim11 = 100.00 - abs(percentChange(eachPattern[10], patForRec[10]))
        sim12 = 100.00 - abs(percentChange(eachPattern[11], patForRec[11]))
        sim13 = 100.00 - abs(percentChange(eachPattern[12], patForRec[12]))
        sim14 = 100.00 - abs(percentChange(eachPattern[13], patForRec[13]))
        sim15 = 100.00 - abs(percentChange(eachPattern[14], patForRec[14]))
        sim16 = 100.00 - abs(percentChange(eachPattern[15], patForRec[15]))
        sim17 = 100.00 - abs(percentChange(eachPattern[16], patForRec[16]))
        sim18 = 100.00 - abs(percentChange(eachPattern[17], patForRec[17]))
        sim19 = 100.00 - abs(percentChange(eachPattern[18], patForRec[18]))
        sim20 = 100.00 - abs(percentChange(eachPattern[19], patForRec[19]))

        sim21 = 100.00 - abs(percentChange(eachPattern[20], patForRec[20]))
        sim22 = 100.00 - abs(percentChange(eachPattern[21], patForRec[21]))
        sim23 = 100.00 - abs(percentChange(eachPattern[22], patForRec[22]))
        sim24 = 100.00 - abs(percentChange(eachPattern[23], patForRec[23]))
        sim25 = 100.00 - abs(percentChange(eachPattern[24], patForRec[24]))
        sim26 = 100.00 - abs(percentChange(eachPattern[25], patForRec[25]))
        sim27 = 100.00 - abs(percentChange(eachPattern[26], patForRec[26]))
        sim28 = 100.00 - abs(percentChange(eachPattern[27], patForRec[27]))
        sim29 = 100.00 - abs(percentChange(eachPattern[28], patForRec[28]))
        sim30 = 100.00 - abs(percentChange(eachPattern[29], patForRec[29]))

        howSim = (sim1+sim2+sim3+sim4+sim5+sim6+sim7+sim8+sim9+sim10+
                  sim11+sim12+sim13+sim14+sim15+sim16+sim17+sim18+sim19+sim20+
                  sim21+sim22+sim23+sim24+sim25+sim26+sim27+sim28+sim29+sim30)/30.00

        if howSim > 60:     # We only want patterns that are greater than 70
            patdex = patternAr.index(eachPattern)   # Find this index number of the current pattern

            patFound = 1

            # TODO Be able to filter patterns just because they are similar 1 point ahead of the prior match.

            print '##################################        @ Data Point', toWhat
            print '##################################     Match Pattern @ Point', patdex
            print 'Current Pattern:', patForRec
            print '==================================='
            print 'Historical Pattern:', eachPattern
            print '----------'
            print '----------'
            print 'Match %:', howSim
            print 'Predicted Outcome %:', performanceAr[patdex]   # Historical Performance of this pattern

            xp = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]

            plotPatAr.append(eachPattern)

            print '##################################'
            print '##################################'

            #'''
        """
        # New one is the same but requires a 50% similarity for the first 10 patterns.

        #'''
        sim1 = 100.00 - abs(percentChange(eachPattern[0], patForRec[0]))
        if sim1 > simreq:
            sim2 = 100.00 - abs(percentChange(eachPattern[1], patForRec[1]))
            if sim2 > simreq:
                sim3 = 100.00 - abs(percentChange(eachPattern[2], patForRec[2]))
                if sim3 > simreq:
                    sim4 = 100.00 - abs(percentChange(eachPattern[3], patForRec[3]))
                    if sim4 > simreq:
                        sim5 = 100.00 - abs(percentChange(eachPattern[4], patForRec[4]))
                        if sim5 > simreq:
                            sim6 = 100.00 - abs(percentChange(eachPattern[5], patForRec[5]))
                            if sim6 > simreq:
                                sim7 = 100.00 - abs(percentChange(eachPattern[6], patForRec[6]))
                                if sim7 > simreq:
                                    sim8 = 100.00 - abs(percentChange(eachPattern[7], patForRec[7]))
                                    if sim8 > simreq:
                                        sim9 = 100.00 - abs(percentChange(eachPattern[8], patForRec[8]))
                                        if sim9 > simreq:
                                            sim10 = 100.00 - abs(percentChange(eachPattern[9], patForRec[9]))
                                            if sim10 > simreq:

                                                sim11 = 100.00 - abs(percentChange(eachPattern[10], patForRec[10]))
                                                if sim11 > simreq:
                                                    sim12 = 100.00 - abs(percentChange(eachPattern[11], patForRec[11]))
                                                    if sim12 > simreq:
                                                        sim13 = 100.00 - abs(percentChange(eachPattern[12], patForRec[12]))
                                                        if sim13 > simreq:
                                                            sim14 = 100.00 - abs(percentChange(eachPattern[13], patForRec[13]))
                                                            if sim14 > simreq:
                                                                sim15 = 100.00 - abs(percentChange(eachPattern[14], patForRec[14]))
                                                                if sim15 > simreq:
                                                                    sim16 = 100.00 - abs(percentChange(eachPattern[15], patForRec[15]))
                                                                    if sim16 > simreq:
                                                                        sim17 = 100.00 - abs(percentChange(eachPattern[16], patForRec[16]))
                                                                        if sim17 > simreq:
                                                                            sim18 = 100.00 - abs(percentChange(eachPattern[17], patForRec[17]))
                                                                            if sim18 > simreq:
                                                                                sim19 = 100.00 - abs(percentChange(eachPattern[18], patForRec[18]))
                                                                                if sim19 > simreq:
                                                                                    sim20 = 100.00 - abs(percentChange(eachPattern[19], patForRec[19]))
                                                                                    if sim20 > simreq:

                                                                                        sim21 = 100.00 - abs(percentChange(eachPattern[20], patForRec[20]))
                                                                                        if sim21 > simreq:
                                                                                            sim22 = 100.00 - abs(percentChange(eachPattern[21], patForRec[21]))
                                                                                            if sim22 > simreq:
                                                                                                sim23 = 100.00 - abs(percentChange(eachPattern[22], patForRec[22]))
                                                                                                if sim23 > simreq:
                                                                                                    sim24 = 100.00 - abs(percentChange(eachPattern[23], patForRec[23]))
                                                                                                    if sim24 > simreq:
                                                                                                        sim25 = 100.00 - abs(percentChange(eachPattern[24], patForRec[24]))
                                                                                                        if sim25 > simreq:
                                                                                                            sim26 = 100.00 - abs(percentChange(eachPattern[25], patForRec[25]))
                                                                                                            if sim26 > simreq:
                                                                                                                sim27 = 100.00 - abs(percentChange(eachPattern[26], patForRec[26]))
                                                                                                                if sim27 > simreq:
                                                                                                                    sim28 = 100.00 - abs(percentChange(eachPattern[27], patForRec[27]))
                                                                                                                    if sim28 > simreq:
                                                                                                                        sim29 = 100.00 - abs(percentChange(eachPattern[28], patForRec[28]))
                                                                                                                        if sim29 > simreq:
                                                                                                                            sim30 = 100.00 - abs(percentChange(eachPattern[29], patForRec[29]))
                                                                                                                            if sim30 > simreq:

                                                                                                                                howSim = (sim1+sim2+sim3+sim4+sim5+sim6+sim7+sim8+sim9+sim10+
                                                                                                                                          sim11+sim12+sim13+sim14+sim15+sim16+sim17+sim18+sim19+sim20+
                                                                                                                                          sim21+sim22+sim23+sim24+sim25+sim26+sim27+sim28+sim29+sim30)/30.00

                                                                                                                                if howSim > patsimreq:
                                                                                                                                    patdex = patternAr.index(eachPattern)   # Find this index number of the current pattern

                                                                                                                                    patFound = 1

                                                                                                                                    # TODO Be able to filter patterns just because they are similar 1 point ahead of the prior match.

                                                                                                                                    print '##################################        @ Data Point', toWhat
                                                                                                                                    print '##################################     Match Pattern @ Point', patdex + 32
                                                                                                                                    print 'Current Pattern:', patForRec
                                                                                                                                    print '==================================='
                                                                                                                                    print 'Historical Pattern:', eachPattern
                                                                                                                                    print '----------'
                                                                                                                                    print '----------'
                                                                                                                                    print 'Match %:', howSim
                                                                                                                                    print 'Predicted Outcome %:', performanceAr[patdex]   # Historical Performance of this pattern

                                                                                                                                    xp = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]

                                                                                                                                    plotPatAr.append(eachPattern)

                                                                                                                                    print '##################################'
                                                                                                                                    print '##################################'

                                                                                                                                    #'''
        """
    predArray = []
    if patFound == 1:
        fig = plt.figure(figsize=(10, 6))

        for eachPat in plotPatAr:
            futurePoints = patternAr.index(eachPat)

            if performanceAr[futurePoints] > patForRec[29]:
                pcolor = '#24bc00'  # Green / Positive
                predArray.append(1.000)
            else:
                pcolor = '#d40000'  # Red / Negative
                predArray.append(-1.000)

            plt.plot(xp, eachPat)
            plt.scatter(35, performanceAr[futurePoints], c=pcolor, alpha=.3)
            predictedOutcomesAr.append(performanceAr[futurePoints])

        predictedAvgOutcome = reduce(lambda x, y: x + y, predictedOutcomesAr) / len(predictedOutcomesAr) # Averages of all perdicted outcomes

        try:
            realOutcomeRange = allData[toWhat + 20:toWhat + 30]
            realAvgOutcome = reduce(lambda x, y: x + y, realOutcomeRange) / len(realOutcomeRange)
            realFutureOutcome = percentChange(allData[toWhat], realAvgOutcome)
            #plt.close()
        except:
            realFutureOutcome = predictedAvgOutcome

        plt.scatter(40, predictedAvgOutcome, c='b', s=25)
        plt.scatter(40, realFutureOutcome, c='#54fff7', s=25)

        plt.plot(xp, patForRec, '#54fff7', linewidth=3)
        plt.grid(True)
        plt.title('Pattern Recognition')

        plt.show()

        # Uses of predArray start here - The purpose of this is essentially to find the prediction average
        predictionAverage = reduce(lambda x, y: x + y, predArray) / len(predArray)  # Average of all predictions (+/-0)

        print ' '
        print 'Statistics:'
        print '----------'
        print predArray
        print 'Number of Matches', len(predArray)
        print 'Prediction Average', predictionAverage
        print 'Predicted Outcome %', predictedAvgOutcome
        print '____________________________________________________________________________________________________________________________________________'
        print ' '

        if realFutureOutcome != predictedAvgOutcome:

            # TODO Note: When the prediction average is = 0, just as many Up as Down...50 - 50 -> no edge, no trade.

            if predictionAverage < 0:
                print 'Drop Predicted'
                print 'Trade @ %', patForRec[29]
                print 'Result %', realFutureOutcome
                if realFutureOutcome < patForRec[29]:
                    accuracyArray.append(100)
                else:
                    accuracyArray.append(0)

            if predictionAverage > 0:
                print 'Rise Predicted'
                print 'Trade @ %', patForRec[29]
                print 'Result %', realFutureOutcome
                if realFutureOutcome > patForRec[29]:
                    accuracyArray.append(100)
                else:
                    accuracyArray.append(0)
        else:
            print '## Prediction Zone ##'

            if predictionAverage < 0:
                print 'Drop Predicted'
            if predictionAverage > 0:
                print 'Rise Predicted'

            print 'Trade @ %', patForRec[29]
            print 'Predicted Result %', predictedAvgOutcome

        print '____________________________________________________________________________________________________________________________________________'
        print ' '

tEnd = time.time() - tStart
print 'Loading Time:',tEnd,'seconds'

def Run(date, price):

    dataLength = len(price)
    print 'Data length:', dataLength

    toWhat = 31  # From beginning of data - to what point are we going to consider

    allData = price

    # Global Variables
    patternAr = []
    performanceAr = []
    patternStorage(allData, patternAr, performanceAr)  # Historical Patterns

    # BACKTESTER

    accuracyArray = []


    while toWhat < dataLength:

        avgLine = allData[:toWhat]  # This specific program will always have data from day 1.

        patForRec = []

        currentPattern(avgLine, patForRec)  # Current Pattern

        patternRecognition(allData, toWhat, patternAr[:(toWhat-32)], performanceAr[:(toWhat-32)], patForRec, accuracyArray)

        #moveOn = raw_input('Press Enter to Continue...')

        toWhat += 1
"""
    print ' '
    print 'Accuracy Array:', accuracyArray
    accuracyAverage = reduce(lambda x, y: x + y, accuracyArray) / len(accuracyArray)
    print 'Backtested Accuracy is', str(accuracyAverage) + '% after', len(accuracyArray), 'actionable trades'
"""




