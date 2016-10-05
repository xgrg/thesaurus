#! /usr/bin/env python
import argparse
import textwrap
import os.path as osp
import tempfile
import os
import numpy as np

def copy_item(i, destdir, doit=False, verbose=True):
    s = i.get('subject')
    f = osp.join(s, s.join(i.fullPath().split(s)[1:])[1:])
    newdir = osp.join(destdir, osp.split(f)[0])

    if not osp.isdir(newdir):
        cmd = 'super-mkdir %s'%newdir
        if verbose:
            print cmd
        if doit:
            os.makedirs(newdir)

    print osp.splitext(i.fullPath())[1]
    if osp.splitext(i.fullPath())[1] == '.mgz':
        cmd = '/home/grg/brainvisa/build/trunk/scripts/runFreesurferCommand.sh /usr/local/freesurfer/FreeSurferEnv.sh mri_convert %s %s' #/home/grg/data/fs/10010/mri/aseg.mgz' '/home/grg/data/fs/10010/mri/aseg.nii'
	tmpf = tempfile.mkstemp(suffix='.nii')
	cmd = cmd%(i.fullPath(), tmpf[1])
	if verbose:
            print cmd
        if doit:
            os.system(cmd)
        cmd = 'mv %s %s'%(tmpf[1], osp.join(destdir, f.replace('.mgz', '.nii')))
        if verbose:
            print cmd
        if doit:
            os.system(cmd)
    else:
        cmd = 'cp %s %s'%(i, osp.join(destdir, f))
        if verbose:
            print cmd
        if doit:
            os.system(cmd)

def backup_freesurfer_subject(subject, tarfile, dbdir, doit=False, verbose=True):
    from brainvisa import axon
    axon.initializeProcesses()
    import neuroHierarchy
    db = neuroHierarchy.databases._databases[dbdir]
    tmpdir = tempfile.mkdtemp()
    if not doit:
        print '##############################################'
        print 'Not doing the job. Just printing the commands.'
        print '##############################################'

    fstypes = ['ResampledWhite', 'ResampledPial', 'ResampledFreesurferThicknessType', 'Freesurfer Cortical Parcellation using Destrieux Atlas', 'Freesurfer aseg']
    if verbose:
        print '=== Collecting data for subject', subject, ' ==='

    for each in fstypes[0:3]:
        for side in ['left', 'right']:
            item = [e for e in db.findDiskItems(_type = each, subject=subject, side=side)]
            if len(item)!=1:
                raise Exception(' Expected one item of type %s found %s (%s)'%(each, len(item), ' - '.join([e.fullPath() for e in item])))
            copy_item(item[0], tmpdir, doit, verbose)
            if verbose:
                print each, side, item

    for each in fstypes[3:]:
        item = [e for e in db.findDiskItems(_type = each, subject=subject)]
        if len(item)!=1:
            raise Exception(' Expected one item of type %s found %s (%s)'%(each, len(item), ' - '.join([e.fullPath() for e in item])))
        copy_item(item[0], tmpdir, doit, verbose)
        print each, item

    mri = [e for e in db.findDiskItems(_type='T1 FreesurferAnat', _format='NIFTI-1 image', subject=subject)]
    if len(mri)!=1:
        raise Exception(' Expected one item of type %s found %s (%s)'%(each, len(item), ' - '.join([e.fullPath() for e in mri])))
    copy_item(mri[0], tmpdir, doit, verbose)
    print 'mri', mri

    opt = 'cvf'
    if osp.splitext(tarfile)[1] == '.gz':
        opt = opt + 'z'
    elif osp.splitext(tarfile)[1] != '.tar':
        tarfile = tarfile + '.tar'
    if verbose:
        print 'Creating %s'%tarfile
    p1, p2 = tmpdir, subject
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
    parser.add_argument("--database", type=str, help='Axon FS database', required=False, default='/home/grg/data/fs')
    parser.add_argument("--doit", dest='doit', help='Do it for real', action='store_true', required=False, default=False)
    parser.add_argument("-v", dest='verbose', action='store_true', required=False, default=True)
    args = parser.parse_args()

    subject = args.subject
    verbose = args.verbose
    tarfile = args.tarfile
    doit = args.doit
    database = args.database

    if tarfile is None:
        tarfile = '/tmp/%s.tar.gz'%subject

    backup_freesurfer_subject(subject, tarfile, database, doit, verbose)







