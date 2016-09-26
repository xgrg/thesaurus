#! /usr/bin/env python
import argparse
import textwrap
import os.path as osp
import json
import os
import os.path as osp

class InputFileMissing(Exception):
    pass

class ALFAHelper(object):
    '''Returns filenames from existing items in the ALFA repository
    or suggests new ones according to the Axon ontology,
    generates commands based on various pipelines steps (parse_command)
    and identifies the last performed step in the processing of a subject'''
    def __init__(self, directory='/home/grg/data/ALFA_DWI', jsonfile='/home/grg/git/alfa/alfa_dwi_pipeline_io_aug2016.json'):
        from brainvisa import axon
        axon.initializeProcesses()
        import neuroHierarchy
        self.__db = neuroHierarchy.databases._databases[directory]
        self.args_types = json.load(open(jsonfile))

    def find_diskitem(self, subject, axontype='Any Type', fmt=None):
        res = self.__db.findDiskItem(exactType=True, **{'_type': axontype, 'subject':subject})
        if res is None:
            if fmt is None:
                raise Exception('No diskitem found. Provide a format to generate a filename for a new item.')
            else:
                res = self.__db.findOrCreateDiskItem(**{'_type': axontype, 'subject':subject, '_format': fmt})
        return res

    def get_ALFA_types(self):
        import neuroProcesses
        return list(set([each.type.name for each in self.__db.findDiskItems(**{'_type': 'Any Type'})]))

    def parse_command(self, subject, name, jsonfile='/home/grg/git/alfa/alfa_dwi_pipeline_aug2016.json'):
        '''Types starting with @ indicate that the corresponding files must exist before execution (ReadDiskItems). \n
        Types starting with > indicate that the corresponding files must exist after execution (WriteDiskItems). \n
        Strings starting with # designate hard-coded filenames.
        Types starting with ! indicate that the filenames will be returned without extension.
        '''
        j = json.load(open(jsonfile))
        types = self.args_types[name]
        dsk = []
        for each in types:
            t = each.strip('@#!>')
            d = t
            if not each.startswith('#'):
                if 'DTIFIT' in t:
                    fmt = 'Directory'
                elif 'Bvec' in t:
                    fmt = 'Bvec file'
                elif 'stats' in t:
                    fmt = 'CSV file'
                else:
                    fmt = 'gz compressed NIFTI-1 image'
                d = self.find_diskitem(subject, t, fmt=fmt).fullPath()
                if each.startswith('@'):
                    if not osp.isfile(d) and not osp.isdir(d):
                        raise InputFileMissing('%s not found (type %s) while declared as input (or remove the leading @)'%(d, t))
                if each.startswith('!'):
                    d = self.find_diskitem(subject, t, fmt=fmt).fullPath()
                    d = d[:d.index('.')]
            dsk.append(d)
        res = parse_command(j[name], dsk)

        return res

    def current_stage(self, subject):
        steps = ['denoising', 'eddycorrect', 'extractb0', 'fslbet.25', 'fslfast', 'denoise_t1', 'spm12', 'dilate', 'ants_t1_to_dwi', 'ants_dwi_to_t1', 'ants_mni_to_t1', 'rotcorr', 'dtifit', 'warp_aal_to_t1', 'warp_aal_to_dwi', 'warp_md_to_t1', 'warp_md_to_mni', 'roistats_md', 'roistats_md_mni']

        def __sort_input_first__(a):
            inp = []
            out = []
            oth = []
            for each in a:
                if each.startswith('@'):
                    inp.append(each)
                elif each.startswith('>'):
                    out.append(each)
                else:
                    oth.append(each)
            res = []
            for each in [inp, out, oth]:
                res.extend(each)
            return res

        existing_all = True
        for i, each in enumerate(steps):
            for filetype in __sort_input_first__(self.args_types[each]):
                t = filetype.strip('@#!>')
                if filetype[0] in '@>':
                    res = [e for e in self.__db.findDiskItems(_type=t, subject=subject)]

                    if len(res) == 0:
                        existing_all = False
                        if filetype.startswith('@'):
                            print subject, 'is stuck at step before', each, '(missing: %s)'%t
                            return '%s-1'%each
                        else:
                            print subject, 'is stuck at step', each, '(missing: %s)'%t
                            return each

        if not existing_all:
            print subject, 'is stuck at step', each
            return each
        print subject, 'is complete'
        return 0

    def generate_batch(self, subjects, step, batchfile, create_workflow=True):
        w = open(batchfile, 'w')
        succeeded = []
        for each in subjects:
	    try:
		w.write('%s\n'%self.parse_command(each, step))
		succeeded.append(each)
	    except InputFileMissing as e:
		print 'Failed', each, e
        w.close()

        if create_workflow:
            try:
                import create_workflow as cw
                import os.path as osp
                cw.create_workflow(batchfile, "%s.workflow"%osp.splitext(batchfile)[0], names=succeeded)
            except ImportError:
                print 'create_workflow command not found. Check that create_workflow.py is in the same folder as thesaurus.'
                raise
        return succeeded

def parse_command(cmd, args):
    if len(args) != cmd.count('%s'):
        raise Exception('%s (%s)\n%s\n%s'%(
            args, len(args),
            cmd,
            'Please check the number of arguments respect the command.'))
    for each in args:
        cmd = cmd.replace('%s', each, 1)
    return cmd

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
	    description=textwrap.dedent('''\
            Associating a command with a unique alias for simple recall.
	    '''))

    parser.add_argument("--cmd", dest='command', type=str, required=False, help='Command')
    parser.add_argument("--name", dest='name', type=str, required=False, help='Command alias')
    parser.add_argument("-n", dest='dontdo',  action="store_true", help='Print the command without running it')
    parser.add_argument("--store", dest='action', action='store_const', const=1)
    parser.add_argument("--run", dest='action', action='store_const', const=2)
    parser.add_argument("--list", dest='action', action='store_const', const=3)
    parser.add_argument("json", type=str, help='JSON file containing all the commands')
    parser.add_argument("args", nargs='*', default=None, type=str, help='Arguments of the command (separated by ;)')
    args = parser.parse_args()

    action = args.action
    if action is None:
        action = 2
    arg = args.args
    name = args.name

    if action == 2:
        # Run command
        j = json.load(open(args.json))
        if args.name is None:
            raise Exception('Command name should be provided')
        if not name in j:
            raise KeyError('Command with key %s not found.'%name)
        cmd = j[name]
        a = arg if not arg is None else []

        cmd = parse_command(cmd, a)
        print cmd
        if not args.dontdo:
            import time
            start_time = time.time()
            res = os.system(cmd)
            print('Command was:\n%s'%cmd)
            if res == 0:
                print('Execution complete. Elapsed time: %f seconds'% (time.time() - start_time))
            elif res == 2:
                print('Execution interrupted. Elapsed time: %f seconds'% (time.time() - start_time))
            print('===')


    elif action == 1:
        #Store command
        if args.name is None:
            raise Exception('Command name should be provided')
        if not arg is None:
            print 'Warning: command called in store mode, provided arguments will get ignored'
        if args.command is None:
            raise Exception('A command should be provided when calling in store mode')
        j = json.load(open(args.json))
        j[name] = args.command
        json.dump(j, open(args.json,'w'), indent=2)

    elif action == 3:
        #List command
        j = json.load(open(args.json))
        from pprint import pprint
        pprint(j, indent=2)



