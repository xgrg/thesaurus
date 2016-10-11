#! /usr/bin/env python
import argparse
import textwrap
import os.path as osp
import tempfile
import os
import os.path as osp
import numpy as np

import pandas as pd
from datetime import datetime

def check_dates(dates):
    is_ante_respected = True
    lastdate = 0
    for d in dates:
        if lastdate > d:
            is_ante_respected = False
            break
        else:
            lastdate = d
    return is_ante_respected

def get_subject_dates(subject, db, types):
    dates = {}
    for t in types:
        dsk = [e for e in db.findDiskItems(_type=t, subject=subject)]
        if len(dsk) > 0:
            mtime = osp.getmtime(dsk[0].fullPath())
            dates[t] = mtime
    return dates

def check_subject2(subject, database, types):
    from brainvisa import axon
    axon.initializeProcesses()
    import neuroHierarchy
    db = neuroHierarchy.databases.database(osp.abspath(database))
    j = json.load(open('/home/grg/git/alfa/alfa_dwi_pipeline_io_aug2016.json'))
    rules = []
    dates = get_subject_dates(subject, db ,types)
    all_ok = True
    for k,v in j.items():
        outputs = [e.strip('>') for e in v if e.startswith('>')]
        inputs = [e.strip('@') for e in v if e.startswith('@')]
        for i in inputs:
            for o in outputs:
                if o in dates and i in dates:
                    if dates[o] < dates[i]:
                       print 'problem with', o,'(%s)'%datetime.fromtimestamp(dates[o]), i, '(%s)'%datetime.fromtimestamp(dates[i]), subject,k
                       all_ok = False


def check_subject(subject, database, types):
    from brainvisa import axon
    axon.initializeProcesses()
    import neuroHierarchy
    db = neuroHierarchy.databases.database(osp.abspath(database))

    dates = get_subject_dates(subject, db, types)

    res = check_dates(dates)


def build_graph(subjects, database, types, verbose=True):
    dates = {}
    from brainvisa import axon
    axon.initializeProcesses()
    import neuroHierarchy
    import pandas as pd
    from datetime import datetime
    db = neuroHierarchy.databases.database(osp.abspath(database))

    mindate = 10000000000
    maxdate = 0

    lines = [], []
    labels = []
    for i, s in enumerate(subjects):
        if verbose and False:
            print s, '(%s/%s)'%(i, len(subjects))
        dates[s] = get_subject_dates(s, db, types)
        stypes = [types.index(e) for e in dates[s].keys()]
        ordered_dates = [dates[s][types[k]] for k in stypes]
        lines[0].extend(pd.to_datetime([datetime.fromtimestamp(e) for e in ordered_dates]))
        lines[1].extend([i]*len(ordered_dates))
        labels.extend(stypes)
        mindate = min(mindate, min(ordered_dates))
        maxdate = max(maxdate, max(ordered_dates))

    lines_by_type = {}, {}
    for x, y ,label in zip(lines[0], lines[1], labels):
        l0, l1 = lines_by_type
        l0.setdefault(label, []).append(x)
        l1.setdefault(label, []).append(y)

    mindate = pd.to_datetime(datetime.fromtimestamp(mindate))
    maxdate = pd.to_datetime(datetime.fromtimestamp(maxdate))

    legends = [types[i] for i in set(labels)]
    plot(subjects, l0, l1, labels, mindate, maxdate, legends)



def plot(subjects, dates, data, val, mindate, maxdate, legends):
    import matplotlib.pyplot as plt
    import matplotlib
    from numpy.random import random, randint
    from datetime import datetime
    matplotlib.rcParams.update({'font.size': 6})

    fig, ax = plt.subplots(figsize=(7,7))
    cmap = matplotlib.cm.get_cmap('rainbow')
    norm = matplotlib.colors.Normalize(vmin=min(val), vmax=max(val))
    m = matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap)

    for i, v in enumerate(set(val)):
        #print i, v, dates[v], data[v]
        rgba = m.to_rgba(v)
        ax.scatter(dates[v], data[v], c=rgba, edgecolor=rgba, marker='s', s=max(5, -0.22*float(len(subjects)) + 25), label=legends[i])
    fig.autofmt_xdate()

    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticklabels(subjects)
    ax.yaxis.set_ticks(xrange(len(subjects)))
    ax.yaxis.set_ticks_position('left')
    plt.legend()
    ax.legend(bbox_to_anchor=(1.14, 1.05))

    import pandas as pd
    day = pd.to_timedelta("1", unit='D')
    plt.xlim(mindate - day, maxdate + day)
    plt.savefig('/tmp/test.svg')
    plt.show()


def get_subject_table(dates, types):
    table = []
    print dates
    for t in types:
        if t in dates.keys():
            table.append((t, datetime.fromtimestamp(dates[t])))
        else:
            table.append((t, 'X'))

    return table


if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
	    description=textwrap.dedent('''\
                    Looks up modification dates from items in an Axon database and checks their
                    conformity with their expected order of antecedency.
	    '''))

    parser.add_argument("database", type=str, help='Axon database')
    parser.add_argument("--subject", type=str, help='subject in the database', required=False)
    parser.add_argument("--json", type=str, help='json describing the global antecedency', required=False)
    parser.add_argument("-v", dest='verbose', action='store_true', required=False, default=True)
    args = parser.parse_args()

    subject = args.subject
    database = args.database
    verbose = args.verbose

    import json
    if args.json is None:
        args.json = '/home/grg/git/alfa/alfa_dwi_pipeline_antecedency.json'

    types = json.load(open(args.json)) #
    from brainvisa import axon
    axon.initializeProcesses()
    import neuroHierarchy
    db = neuroHierarchy.databases.database(osp.abspath(database))

    if subject is None:
        subjects = sorted(list(set([e.get('subject') for e in db.findDiskItems(_type=types[0])]))) #['10010', '10015']
        ans = raw_input('do it for all subjects? %s'%subjects)
    else:
	dates = get_subject_dates(subject, db, types)
        table = get_subject_table(dates, types)
        f = open('/tmp/test.html','w')
        f.write(pd.DataFrame(table).to_html())
        f.close()

        subjects = [subject] #sorted([e.get('subject') for e in db.findDiskItems(_type=types[0])]) #['10010', '10015']

    for s in subjects:
        check_subject2(s, database, types)

    build_graph(subjects, database, types)









