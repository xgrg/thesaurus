#! /usr/bin/env python
import argparse
import textwrap
import dicom
import scandir
import os.path as osp
import shutil
import os, sys
import pandas as pd

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
	description=textwrap.dedent('''\
	Performs various operations across a series of DICOM files.

        Read: compiles a table with the values of a given tag across a DICOM collection
        Swap: Given two tags, swaps their value across an entire DICOM collection
        Remove: Clears out any existing value given a tag in a DICOM collection

        If a csv file is passed to the option --csv, then a table will be generated with
        a backup of the previous state before clearing/swapping (or just the result of
        the reading operation)
	'''))

parser.add_argument("-i", dest='source', type=str, required=True)
parser.add_argument("-t1", dest='first_tag', type=str, required=True)
parser.add_argument("-t2", dest='second_tag', type=str, required=False)
parser.add_argument("--value", dest='value', type=str, required=False)
parser.add_argument("--remove", dest='action', action='store_const', const=2)
parser.add_argument("--swap", dest='action', action='store_const', const=1)
parser.add_argument("--read", dest='action', action='store_const', const=3)
parser.add_argument("--csv", dest='csv', type=str, required=False)
args = parser.parse_args()

backup_archive = '/tmp/backup.tar.gz'
source = osp.abspath(args.source)
t1 = args.first_tag
t2 = args.second_tag
csv = args.csv
value = args.value
if value is None:
    value = ''

action = args.action
if action is None:
    action = 1
print action

def collect_dicom(source):
    ''' If source is a file then do nothing, if a directory then returns the list of existing dcm files'''
    if not ((osp.isfile(source) and source.endswith('.dcm')) or osp.isdir(source)):
        raise Exception('%s should be an existing DCM file or directory'%source)
    if osp.isfile(source):
        dcm = [source]

    elif osp.isdir(source):
        dcm = []
        for root, dirs, files in scandir.walk(source):
            dcm.extend([osp.join(root, f) for f in files if f.endswith('.dcm')])
    return dcm


def readtag(source, tag):
    ''' Swaps values from two tags in a DICOM file or a directory'''
    dcm = collect_dicom(source)
    table = [['PatientID', 'tag', 'tag_value', 'filepath']]

    for i, each in enumerate(dcm):
        progress = i/float(len(dcm)) * 100.0
        sys.stdout.write("Operation progress: %d%%   \r" % (progress) )
        sys.stdout.flush()

        try:
            d = dicom.read_file(each)
            tagval = getattr(d, tag)
            pid = d.PatientID
            table.append([pid, tag, tagval, each])

        except (dicom.filereader.InvalidDicomError, IOError) as e:
            print 'WARNING: file %s raised the following error:\n%s'%(each, e)
        except KeyboardInterrupt:
            print '<Keyboard Interrupt>'
            df = pd.DataFrame(table[1:], columns=table[0])
            return df
        except Exception as e:
            print e
            df = pd.DataFrame(table[1:], columns=table[0])
            return df
    df = pd.DataFrame(table[1:], columns=table[0])
    return df



def swap(source, t1, t2, force=False, backup=True):
    ''' Swaps values from two tags in a DICOM file or a directory'''
    if backup:
        print 'Backup to ', backup_archive
        os.system('tar cfz %s %s'%(backup_archive, source))
    dcm = collect_dicom(source)
    table = [['PatientID', 'first_tag', 'tag1_value', 'second_tag', 'tag2_value', 'filepath']]

    print 'WARNING: will swap tags %s and %s in the following files:\n%s\n(%s files)'\
        %(t1, t2, '\n'.join(dcm), len(dcm))
    if (force or raw_input('Proceed? y/N ') == 'y'):
        for i, each in enumerate(dcm):
            progress = i/float(len(dcm)) * 100.0
            sys.stdout.write("Operation progress: %d%%   \r" % (progress) )
            sys.stdout.flush()

            try:
                d = dicom.read_file(each)
                first = getattr(d, t1)
                second = getattr(d, t2)
                pid = d.PatientID

                table.append([pid, t1, first, t2, second, each])
                setattr(d, t2, first)
                setattr(d, t1, second)
                dicom.write_file(each, d)

            except (dicom.filereader.InvalidDicomError, IOError) as e:
                print 'WARNING: file %s raised the following error:\n%s'%(each, e)
            except KeyboardInterrupt:
                print '<Keyboard Interrupt>'
                df = pd.DataFrame(table[1:], columns=table[0])
                return df
            except Exception as e:
                print e
                df = pd.DataFrame(table[1:], columns=table[0])
                return df
        df = pd.DataFrame(table[1:], columns=table[0])
        return df


def remove(source, tag, value='', force=False, backup=False):
    ''' Clears the value of a given tag in a DICOM file or directory and replaces
    it with a new value (default='')'''
    if backup:
        print 'Backup to ', backup_archive
        os.system('tar cfz %s %s'%(backup_archive, source))
    dcm = collect_dicom(source)
    table = [['PatientID', 'removed_tag', 'tag_value', 'filepath']]

    print 'WARNING: will remove tag %s from the following files:\n%s\n(%s files)'\
        %(tag, '\n'.join(dcm), len(dcm))
    if (force or raw_input('Proceed? y/N ') == 'y'):
        for i, each in enumerate(dcm):
            progress = i/float(len(dcm)) * 100.0
            sys.stdout.write("Operation progress: %d%%   \r" % (progress) )
            sys.stdout.flush()
            try:
                d = dicom.read_file(each)
                pid = d.PatientID
                tagval =  getattr(d, tag)
                table.append([pid, tag, tagval, each])
                setattr(d, tag, value)
                dicom.write_file(each, d)
            except (dicom.filereader.InvalidDicomError, IOError) as e:
                print 'WARNING: file %s raised the following error:\n%s'%(each, e)
            except KeyboardInterrupt:
                print '<Keyboard Interrupt>'
                df = pd.DataFrame(table[1:], columns=table[0])
                return df
            except Exception as e:
                print e
                df = pd.DataFrame(table[1:], columns=table[0])
                return df

        df = pd.DataFrame(table[1:], columns=table[0])
        return df


if (action == 1):
    df = swap(source, t1, t2)
elif (action == 2):
    df = remove(source, t1, value)
elif (action == 3):
    df = readtag(source, t1)

if not csv is None:
    df.to_csv(csv)
