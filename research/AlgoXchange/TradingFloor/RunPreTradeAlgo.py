
fx = True

if fx:

    from Chit.XeQT.PreTradeAlgoFX import *

    tstart = time.time()


    "Pre Trade Algo ----------------------------- Inputs"


    # Setup(price, timeframe, a, b, strategy, cp, targets, jpy?)

    # Majors
    #EURUSD = Setup(1.10289, "4hr", 1.11861, 1.10021, 1, 50, [1.11427, 1.11861], False)
    #USDJPY = Setup(105.178, "30min", 106.122, 105.215, 1, 50, [105.670], True)
    #GBPUSD = Setup(1.30388, "30min", 1.30863, 1.30343, 1, 50, [1.30601, 1.30863], False)
    #USDCHF = Setup(0.98197, "2hr", 0.97266, 0.98306, 1, 50, [0.97897, 0.97638], False)
    #USDCAD = Setup(1.29615, "1hr", 1.28612, 1.29872, 1, 50, [1.29257, 1.28714], False)
    #AUDUSD = Setup(0.75759, "D", 0.71484, 0.76474, 1, 50, [0.74948, 0.73018], False)
    #NZDUSD = Setup(0.70485, "D", 0.72984, 0.69633, 2, 50, [0.71137, 0.72197], False)

    # Minors
    #GBPCAD = Setup(1.71986, "4hr", 1.74533, 1.70448, 1, 50, [1.71499, 1.72522, 1.73508], False)
    Setup(1.26395, "2hr", 1.24423, 1.26270, 1, 50, [1.25814, 1.25353], False)
    # Euro Crosses
    Setup(0.86172, "1hr", 0.86918, 0.86091, 1, 50, [0.8636, 0.86687], False)
    #EURCHF = Setup(1.08958, "4hr", 1.08056, 1.09382, 2, 50, [1.08971, 1.08578, 1.09379], False)
    # Yen Crosses
    Setup(140.363, "1hr", 138.341, 140.784, 1, 50, [139.944, 139.307], True)
    Setup(74.202, "4hr", 71.131, 74.270, 2, 50, [72.977, 72.140], True)
    Setup(77.650, "2hr", 78.429, 77.61, 2, 50, [77.856, 78.183], True)

    #  Aussie Crosses

    #securities.append(EURUSD)
    #securities.append(USDJPY)
    #securities.append(GBPUSD)
    #securities.append(USDCHF)
    #securities.append(USDCAD)
    #securities.append(AUDUSD)
    #securities.append(NZDUSD)

    #securities.append(GBPCAD)
    #securities.append(GBPCHF)
    #securities.append(EURGBP)
    #securities.append(EURCHF)
    #securities.append(GBPJPY)
    #securities.append(ZDJPY)
    #securities.append(CADJPY)

    tend = time.time() - tstart

    #TS = M.tradestats(M.ENTRYLIMIT, M.MaxLoss, M.ATR, M.Side, M.Div, M.Targets, M.CP)

    for i in securities:
        entry = i.fixedentry(i.InnerZone, i.OuterZone)
        fixedentries.append(entry)

    for x in range(0, len(securities)):
        print securities[x]
        print "### Fixed ENTRY:", fixedentries[x]
        print '________________________________###'
        print ""


    print '~/Chit$: "Pre Trade ROE Check"'
    print 'Processing Time:', tend, 'seconds'
    print '____________________________________'
    print ''


else:

    from Chit.XeQT.PreTradeAlgoOld import *

    tstart = time.time()

    # Setup(price, atr, a, b, strategy, cp, targets)

    #CSCO = Setup(29.81, 0.1524, 28.17, 29.99, 1, 50, [29.24, 28.63])
    #FSLR = Setup(43.82, 1.1022, 49.27, 42.77, 1, 50, [44.54, 46.54])
    #GOOG = Setup(719.76, 4.6659, 688.5, 723.75, 1, 50, [710.52, 698.68])
    #FB = Setup(116.85, 1.3593, 108.23, 118.69, 1, 50, [115.87, 112.92])  # 4HR ATR = 1.3593
    #AAPL = Setup(98.78, 1.3357, 89.47, 100.73, 1, 50, [96.84, 91.45])  # 4HR ATR = 1.3357
    BIDU = Setup(165.2, 3.3291, 167.75, 156.26, 1, 50, [159.15, 162.29])
    AMZN = Setup(770.14, 8.8699, 734.05, 770.45, 1, 50, [757.03, 750.32])
    #PYPL = Setup(39.33, 0.5476, 35.73, 40.07, 1, 50, [38.64, 37.39])
    #V = Setup(80.11, 0.2619, 77.54, 79.99, 1, 50, [79.32, 78.67])


    tend = time.time() - tstart

    #TS = M.tradestats(M.ENTRYLIMIT, M.MaxLoss, M.ATR, M.Side, M.Div, M.Targets, M.CP)
    #print CSCO
    #print FSLR
    #print GOOG
    #print FB
    #print AAPL
    print BIDU
    print AMZN
    #print PYPL
    #print V

    #A = CSCO.fixedentry(CSCO.InnerZone, CSCO.OuterZone)
    #B = FSLR.fixedentry(FSLR.InnerZone, FSLR.OuterZone)
    #C = GOOG.fixedentry(GOOG.InnerZone, GOOG.OuterZone)
    #D = FB.fixedentry(FB.InnerZone, FB.OuterZone)
    #E = AAPL.fixedentry(AAPL.InnerZone, AAPL.OuterZone)
    F = BIDU.fixedentry(BIDU.InnerZone, BIDU.OuterZone)
    G = AMZN.fixedentry(AMZN.InnerZone, AMZN.OuterZone)
    #H = PYPL.fixedentry(PYPL.InnerZone, PYPL.OuterZone)
    #I = V.fixedentry(V.InnerZone, V.OuterZone)

    print ""
    print 'Entries under fixed entry strategy:'
    #print A
    #print B
    #print C
    #print D
    #print E
    print F
    print G
    #print H
    #print I
    print ""

    print '~/Chit$: "Pre Trade ROE Check"'
    print 'Processing Time:', tend, 'seconds'
    print '____________________________________'
    print ''

