""" Decision Support System """

from Chit.LearnAI.tradingIntelligence import *

context = MorningSpike(["TSLA"])
data = Data(context)

start = '2010-02-14'
end = '2017-02-15'

#SR = ResSup(data.history)

smooth = []
d1 = []
d2 = []

for each in data.securityList:
    # Smoothed Closing Price
    data.history["{} Smooth".format(str(each))] = data.history[each].rolling(window = 20, center = False).mean()
    smooth.append("{} Smooth".format(str(each)))

for each in smooth:
    # 1st Derivative
    data.history["{} Dx".format(str(each))] = data.history[each].diff()
    d1.append("{} Dx".format(str(each)))

for each in d1:
    # 2nd Derivative
    data.history["{}2".format(str(each))] = data.history[each].diff()
    d2.append("{}2".format(str(each)))

#data = Data(DoubleBottom())


# Fill in Missing Data
data.history.ffill(inplace=True)
data.history.bfill(inplace=True)

print data.history


plot_data(data.history)

#plot_selected(data.history.ix[data.history.index.indexer_between_time(datetime.time(8), datetime.time(3))], data.securityList, start, end)

plot_selected(data.history, d1, start, end)
plot_selected(data.history, d2, start, end)
