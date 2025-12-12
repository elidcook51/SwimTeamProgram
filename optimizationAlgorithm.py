import pandas as pd
import seedingHelp as help
import numpy as np
from amplpy import AMPL
import champsSeedingAlgorithm as seeder

allData = pd.read_csv("C:/Users/ucg8nb/Downloads/2025 Data Transform.csv")

testData = seeder.scoreOneTeam(allData, [13,14], 'W', 'CITY')
# testData = seeder.dataframePlaceToScore(testData)

# testData.to_csv('C:/Users/ucg8nb/Downloads/Test Data 6003.csv')

# testData = pd.read_csv('C:/Users/ucg8nb/Downloads/Test Data 6003.csv')

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
    print(x_vals)

def relayProgram(testData):
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

    subject to relayMembership {s in S, m in M}: z[s,m] = sum{t in T} inc[s,t] * y[m,t]
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



noRelayProgram(seeder.dataframePlaceToScore(testData))
