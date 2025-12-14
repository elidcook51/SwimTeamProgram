import pandas as pd
import seedingHelp as help
import numpy as np
from amplpy import AMPL
import individualScore as individualSeed
import relayHelp as relays


def noRelayProgram(testData):
    events = help.getStrokes()
    records = []
    for _, row in testData.iterrows():
         s = row['Swimmer']
         for e in events:
              pts = row[e]
              records.append({'s': s, "e":e, "p":pts})

    long_df = pd.DataFrame(records)

    setupCode = r"""
    set S; set E; 
    param p{S,E};

    var x{S,E} binary;

    maximize points: sum {s in S} sum {e in E} x[s,e] * p[s,e];

    subject to limitSwim {s in S}: sum {e in E} x[s,e] <= 3;
    subject to limitEvent {e in E}: sum {s in S} x[s,e] <= 2;
    """

    ampl = AMPL()
    ampl.setOption('solver', 'highs')
    ampl.eval(setupCode)

    ampl.set['S'] = testData['Swimmer'].tolist()
    ampl.set['E'] = events

    p_series = long_df.set_index(['s', 'e'])['p']

    ampl.getParameter('p').setValues(p_series)

    ampl.solve()

    x_vals = ampl.getVariable('x').getValues().toPandas()
    return x_vals

def getThreeEventSwimmers(testData):
    x_vals = noRelayProgram(testData)
    x_vals = x_vals[x_vals['x.val'] > 0.5]
    x_vals = x_vals.reset_index()
    x_vals = x_vals.rename(columns={"index0": "Swimmer", "index1": "Event", "value": "Chosen"})
    swimmers = x_vals['Swimmer'].unique().tolist()
    threeSwim = []
    for s in swimmers:
        tempDf = x_vals[x_vals['Swimmer'] == s]
        if len(tempDf) == 3:
            threeSwim.append(s)
    return threeSwim

def relayProgram(testData, relayData, incData):
    setupCode = r"""
    
    set S; set E; set M; set T;

    param p{S,E}; param r{M, T}; param inc{S, T} binary;

    var x{S,E} binary;
    var y{M, T} binary;
    var z{S,M} binary;

    maximize points: (sum{s in S} sum {e in E} x[s,e] * p[s,e]) + (sum {m in M} sum {t in T} y[m, t] * r[m, t]);

    subject to limitEvent {e in E}: sum {s in S} x[s,e] <= 2;
    subject to limitRelay {m in M}: sum {t in T} y[m, t] <= 1;
    subject to limitSwimmer {s in S}: sum {e in E} x[s,e] <= 3;  
    subject to totalLimitSwimmer {s in S}: (sum {e in E} x[s,e]) + (sum {m in M} z[s,m]) <= 4;

    subject to relayMembership {s in S, m in M}: z[s,m] = sum{t in T} inc[s,t] * y[m,t];
    """

    events = help.getStrokes()
    swimmers = testData['Swimmer'].tolist()

    rows = []
    for _, row in testData.iterrows():
         s = row['Swimmer']
         for e in events:
              pts = row[e]
              rows.append({"s":s, "e":e, "p": pts})
    p_df = pd.DataFrame(rows)

    teams = relayData['Team'].astype(str).unique().tolist()

    r_df = relayData[['m', 'Team', 'r']].copy()
    r_df['Team'] = r_df['Team'].astype(str)

    ampl = AMPL()
    ampl.setOption('solver', 'highs')
    ampl.eval(setupCode)

    ampl.set['S'] = swimmers
    ampl.set['E'] = events
    ampl.set['M'] = ['m', 'f']
    ampl.set['T'] = teams

    ampl.getParameter('p').setValues(p_df.set_index(['s', 'e'])['p'])
    ampl.getParameter('r').setValues(r_df.set_index(['m', 'Team'])['r'])
    ampl.getParameter('inc').setValues(incData.set_index(['s', 't'])['inc'])

    ampl.solve()

    x_vals = ampl.getVariable('x').getValues().toPandas()
    y_vals = ampl.getVariable('y').getValues().toPandas()
    z_vals = ampl.getVariable('z').getValues().toPandas()
    obj_val = ampl.getObjective('points').value()

    
    return x_vals, y_vals, obj_val



# allData = pd.read_csv("C:/Users/ucg8nb/Downloads/2025 Data Transform.csv")
# testData = individualSeed.scoreOneTeam(allData, [13,14], 'W', 'CITY')
# testData = individualSeed.dataframePlaceToScore(testData)
# relayPos = relays.buildRelayPositions(allData, [13,14], 'W', 'CITY', getThreeEventSwimmers(testData))
# swimmers = testData['Swimmer'].tolist()
# incData = relays.buildInc(relayPos, swimmers)
# # print(len(incData))
# x_vals = noRelayProgram(testData)
# relayProgram(testData, relayPos, incData)



