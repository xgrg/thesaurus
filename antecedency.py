#! /usr/bin/env python
import argparse
import textwrap
import os.path as osp
import tempfile
import os
import os.path as osp
import numpy as np
import json
import pandas as pd
from datetime import datetime

def get_subject_dates(subject, db, types, datetype='c'):
    ''' Given a subject, an Axon Database and a list of Axon types,
    collects corresponding DiskItems and return their system dates in a dictionary.'''
    if not datetype in 'mc':
        raise Exception('datetype should be either m (modification) or c (creation)')
    dates = {}
    for t in types:
        dsk = [e for e in db.findDiskItems(_type=t, subject=subject)]
        if len(dsk) > 0:
            if datetype == 'm':
                mtime = osp.getmtime(dsk[0].fullPath())
            elif datetype == 'c':
                mtime = osp.getctime(dsk[0].fullPath())
            dates[t] = mtime
    return dates

def collect_types(jsonfile):
    j = json.load(open(jsonfile))
    types = set()
    for k,v in j.items():
        for i in v:
            if i[0] in '>@!#':
                i = i[1:]
            types.add(i)
    return list(types)


def check_subject(subject, database, jsonfile, antecfile, verbose=True):
    ''' Given a subject, the path to a database and a JSON file describing
    input/outputs of a pipeline, checks'''
    from brainvisa import axon
    axon.initializeProcesses()
    import neuroHierarchy
    db = neuroHierarchy.databases.database(osp.abspath(database))
    j = json.load(open(jsonfile))
    types = json.load(open(antecfile)) #collect_types(jsonfile)
    dates = get_subject_dates(subject, db ,types)

    issues = []
    for k,v in j.items():
        outputs = [e.strip('>') for e in v if e.startswith('>')]
        inputs = [e.strip('@') for e in v if e.startswith('@')]
        for i in inputs:
            for o in outputs:
                if o in dates and i in dates:
                    if dates[o] < dates[i]:
                       if verbose:
                           print 'problem with', o,'(%s)'%datetime.fromtimestamp(dates[o]), i, '(%s)'%datetime.fromtimestamp(dates[i]), subject,k
                       issues.append((o, datetime.fromtimestamp(dates[o]), i, datetime.fromtimestamp(dates[i]), subject, k))
    return issues


def build_graph(subjects, database, types, verbose=True):
    from brainvisa import axon
    axon.initializeProcesses()
    import neuroHierarchy
    db = neuroHierarchy.databases.database(osp.abspath(database))

    dates = {}
    lines = [], []
    steps = []
    for i, s in enumerate(subjects):
        if verbose and False:
            print s, '(%s/%s)'%(i, len(subjects))
        dates[s] = get_subject_dates(s, db, types)
        stypes = [types.index(e) for e in dates[s].keys()]
        ordered_dates = [dates[s][types[k]] for k in stypes]
        if len(stypes) == 0:
            print 'no items found for subject', s
            continue
        lines[0].extend(pd.to_datetime([datetime.fromtimestamp(e) for e in ordered_dates]))
        lines[1].extend([i]*len(ordered_dates))
        steps.extend(stypes)


    l0, l1 = {}, {}
    for x, y ,label in zip(lines[0], lines[1], steps):
        l0.setdefault(label, []).append(x)
        l1.setdefault(label, []).append(y)

    legends = [types[i] for i in set(steps)]
    plot(subjects, l0, l1, steps, legends)



def plot(subjects, dates, ysubj, steps, legends):
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.rcParams.update({'font.size': 6})

    fig, ax = plt.subplots(figsize=(7,7))
    cmap = matplotlib.cm.get_cmap('rainbow')
    norm = matplotlib.colors.Normalize(vmin=min(steps), vmax=max(steps))
    m = matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap)

    for i, v in enumerate(set(steps)):
        rgba = m.to_rgba(v)
        ax.scatter(dates[v], ysubj[v], c=rgba, edgecolor=rgba, marker='s', s=max(5, -0.22*float(len(subjects)) + 25), label=legends[i])
    fig.autofmt_xdate()

    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticklabels(subjects)
    ax.yaxis.set_ticks(xrange(len(subjects)))
    ax.yaxis.set_ticks_position('left')

    class Formatter(object):
	def __init__(self, *args):
	    self.args = args
	def __call__(self, y):
	    subjects = self.args[1]
            subject = ''
            if y > 0 and y < len(subjects):
                subject = subjects[int(y)]
            else:
                subject = ''
	    return subject

    import matplotlib.dates as mdates
    ax.format_ydata = Formatter(dates, subjects)
    ax.format_xdata = mdates.DateFormatter('%Y-%m-%d')

    plt.legend()
    ax.legend(bbox_to_anchor=(1.14, 1.05))

    plt.show()


def get_subject_table(dates, types):
    table = []
    for t in types:
        v = (t, datetime.fromtimestamp(dates[t])) if t in dates.keys() else (t, 'X')
        table.append(v)
    return table


if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
	    description=textwrap.dedent('''\
                    Looks up modification dates from items in an Axon database and checks their
                    conformity with their expected order of antecedency.
	    '''))

    parser.add_argument("database", type=str, help='Axon database')
    parser.add_argument("--subject", type=str, help='subject in the database', required=False)
    parser.add_argument("--json", type=str, help='json describing the various steps of the pipeline', required=False)
    parser.add_argument("--order", type=str, help='json describing the global antecedency', required=False)

    parser.add_argument("-v", dest='verbose', action='store_true', required=False, default=True)
    args = parser.parse_args()

    subject = args.subject
    database = args.database
    verbose = args.verbose

    jsonfile = args.json
    antecfile = args.order
    if args.order is None:
        antecfile = '/home/grg/git/alfa/alfa_dwi_pipeline_antecedency.json'
    if args.json is None:
        jsonfile = '/home/grg/git/alfa/alfa_dwi_pipeline_io_aug2016.json'

    from brainvisa import axon
    axon.initializeProcesses()
    import neuroHierarchy
    db = neuroHierarchy.databases.database(osp.abspath(database))
    #types = collect_types(jsonfile)
    types = json.load(open(antecfile))

    if subject is None:
        subjects = sorted(list(set([e.get('subject') for e in db.findDiskItems(_type='Any Type')]))) #['10010', '10015']
        ans = raw_input('do it for all subjects? %s'%subjects)
    else:
	dates = get_subject_dates(subject, db, types)

        table = get_subject_table(dates, types)
        f = open('/tmp/test.html','w')
        f.write(pd.DataFrame(table).to_html())
        f.close()

        subjects = [subject]

    for s in subjects:
        check_subject(s, database, jsonfile, antecfile)

    build_graph(subjects, database, types)









