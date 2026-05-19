from Tanulytics.Connect.GettingData.IntraDay_Google import get_google_data
from Tanulytics.LearnAI.PyChitPatternRecognition import *
from Tanulytics.LearnAI.PyChitPatterns import *

rawdata = get_google_data("TSLA", 3600, 20000)

extract = rawdata.values[:,0]

patternAr, performanceAr = getpatterns(extract, 30)


fromend = 1

#patForRec = patterns.patternAr[patterns.n-1]
patForRec = patternAr[len(patternAr)-fromend]
allPatterns = patternAr[0:len(patternAr)-fromend]
accuracyArray = []


'''
#Pattern Check
x = extract[len(extract)-30:]
x = x/x[0]
xres = x-1

plt.plot(x)
plt.show()
plt.plot(xres)
plt.show()

plt.plot(patForRec)
plt.show()

'''

#print patterns.performanceAr


"""
plt.plot(patterns.patternAr[patterns.n-1], '#54fff7', linewidth=3)
#plt.scatter(35, patterns.performanceAr[patterns.n-1], c='#24bc00', alpha=.3)

plt.title("Current Pattern")
plt.grid(True)
plt.show()
"""

ML_Analysis = PatRec(patForRec, allPatterns, performanceAr, accuracyArray)

#totalStart = time.time()
#Run(data, data)
#totalEnd = time.time()-totalStart

#print '_________________________________________________________'

#print 'Entire processing took:',totalEnd,'seconds'
#'''
