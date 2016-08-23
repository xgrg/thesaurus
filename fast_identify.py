#! /usr/bin/env python
import argparse
import textwrap
import os.path as osp
import tempfile
import os
import numpy as np

def identify_tissues(fast, b0, doit=False, verbose=True):
    code, tmpfile = tempfile.mkstemp(suffix='.csv')
    cmd = 'AimsRoiFeatures -i %s -s %s -o %s'%(fast, b0, tmpfile)
    if verbose:
        print cmd
    os.system(cmd)
    n = np.genfromtxt(tmpfile, delimiter='\t', names=True)
    minvol = 1000000000000000.0
    minmean = 100000000000000.0
    csv = -1
    white = -1
    for line in n:
        if line['volume'] < minvol:
            minvol = float(line['volume'])
            csf = int(line['ROI_label'])
        elif line['mean'] < minmean:
            minmean = float(line['mean'])
            white = int(line['ROI_label'])

    grey = list(set([3,2,1]).difference(set([csf, white])))[0]

    if verbose:
        print 'labels: grey', grey, 'white', white, 'csf', csf
    changed = []
    if [csf, white, grey] != [1,2,3]:
        changed.append(subject)
        if verbose:
            print 'INVERTED !'
    grey = grey - 1
    white = white - 1
    csf = csf - 1

    f = fast.split('_seg')
    headers = ['csf', 'white', 'grey']
    if verbose:
        print 'initial'
    olds = ['%s_seg_%s%s'%(f[0], csf, f[1]),
            '%s_seg_%s%s'%(f[0], white, f[1]),
            '%s_seg_%s%s'%(f[0], grey, f[1])]
    if verbose:
        print zip(headers, olds)

        print 'final'
    news = ['%s_seg_%s%s'%(f[0], 0, f[1]),
            '%s_seg_%s%s'%(f[0], 1, f[1]),
            '%s_seg_%s%s'%(f[0], 2, f[1])]
    if verbose:
        print zip(headers, news)

    for old in olds:
        cmd = 'mv %s %s.backup'%(old, old)
        if verbose:
            print cmd
        if doit:
            os.system(cmd)
    for old, new in zip(olds, news):
        cmd = 'mv %s.backup %s'%(old, new)
        if verbose:
            print cmd
        if doit:
            os.system(cmd)


def identify_tissues_axon(subject, database='/home/grg/data/ALFA_DWI', doit=False, verbose=True):
    from brainvisa import axon
    axon.initializeProcesses()
    import neuroHierarchy
    db = neuroHierarchy.databases._databases[database]
    fast = [e for e in db.findDiskItems(_type='ALFA DWI B0 Brain FSL FAST', subject=subject)][0].fullPath()
    b0 = [e for e in db.findDiskItems(_type='ALFA DWI B0 Map', subject=subject)][0].fullPath()
    identify_tissues(fast, b0, doit, verbose)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
	    description=textwrap.dedent('''\
            FSL tends to swap labels to identify grey, white matter or CSF and the produces files consequently.
            This command identifies the labels out from FSL FAST results in an Axon database and renames the
            output files respecting the model seg_0:csf seg_1:white seg_2:grey.
	    '''))

    parser.add_argument("subject", type=str, help='subject in the Axon database')
    parser.add_argument("--database", type=str, help='Axon database', required=False)
    parser.add_argument("-v", dest='verbose', action='store_true', required=False, default=True)
    parser.add_argument("-n", dest='dontdoit', action='store_true', required=False, help='Identifies the labels but stops before renaming the files')
    args = parser.parse_args()

    subject = args.subject
    database = args.database
    verbose = args.verbose
    dontdoit = args.dontdoit
    if database is None:
        database = '/home/grg/data/ALFA_DWI'

    identify_tissues_axon(subject, database, not dontdoit, verbose)







