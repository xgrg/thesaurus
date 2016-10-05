#! /usr/bin/env python
import argparse
import textwrap
import os.path as osp
import tempfile
import os
import numpy as np

def find_empty_dirs(root_dir='.'):
    for dirpath, dirs, files in os.walk(root_dir):
        if not dirs and not files:
            yield dirpath

def backup_subject_axon(subject, tarfile, database, doit=False, verbose=True, remove=False):
    from brainvisa import axon
    axon.initializeProcesses()
    import neuroHierarchy
    db = neuroHierarchy.databases._databases[database]
    items = [e for e in db.findDiskItems(_type='Any Type', subject=subject)]
    items = [e.fullPath() for e in items if e.get('subject')]

    tmpdir = osp.join(tempfile.mkdtemp(), osp.split(database)[1])
    action = 'cp' if not remove else 'mv'


    if verbose:
        print 'Found %s items'%len(items)
        print items

    if not doit:
        print '##############################################'
        print 'Not doing the job. Just printing the commands.'
        print '##############################################'

    for i in items:
        f = i.split(database)[1][1:]
        newdir = osp.join(tmpdir, osp.split(f)[0])
        if not osp.isdir(newdir):
            cmd = 'super-mkdir %s'%newdir
            if verbose:
                print cmd
            if doit:
                os.makedirs(newdir)
        cmd = 'cp %s %s'%(i, osp.join(tmpdir, f))
        if verbose:
            print cmd
        if doit:
            os.system(cmd)

        if remove:
            db.removeDiskItem(db.createDiskItemFromFilename(i), eraseFiles=True)


    if action == 'mv':
        removed = 0
        for i in items:
            if not osp.exists(i):
                removed += 1
        if verbose:
            print 'Removed %s files out of %s'%(removed, len(items))
	    emptydirs = list(find_empty_dirs(database))
	    print len(emptydirs), 'empty directories in %s (%s)'%(database, ', '.join(emptydirs))

    opt = 'cvf'
    if osp.splitext(tarfile)[1] == '.gz':
        opt = opt + 'z'
    elif osp.splitext(tarfile)[1] != '.tar':
        tarfile = tarfile + '.tar'
    if verbose:
        print 'Creating %s'%tarfile
    p1, p2 = osp.split(tmpdir)
    cmd = 'tar %s %s -C %s %s'%(opt, tarfile, p1, p2)
    if verbose:
        print cmd
    if doit:
        os.system(cmd)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
	    description=textwrap.dedent('''\
                    Builds an archive from all items associated with some subject from an Axon database.
	    '''))

    parser.add_argument("subject", type=str, help='subject in the Axon database')
    parser.add_argument("--tarfile", type=str, help='tar archive to create', required=False)
    parser.add_argument("--database", type=str, help='Axon database', required=False, default='/home/grg/data/ALFA_DWI')
    parser.add_argument("-v", dest='verbose', action='store_true', required=False, default=True)
    parser.add_argument("--doit", dest='doit', action='store_true', required=False, help='Identifies the labels but stops before renaming the files', default=False)
    parser.add_argument("--remove", dest='remove', action='store_true', required=False, help='Removes the subject from the database or simply build a backup', default=False)
    args = parser.parse_args()

    subject = args.subject
    database = args.database
    verbose = args.verbose
    tarfile = args.tarfile
    doit = args.doit
    remove = args.remove
    if tarfile is None:
        tarfile = '/tmp/%s.tar.gz'%subject

    backup_subject_axon(subject, tarfile, database, doit, verbose, remove)







