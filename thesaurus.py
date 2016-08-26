#! /usr/bin/env python
import argparse
import textwrap
import os.path as osp
import json
import os
import os.path as osp

class ALFAHelper(object):
    '''Returns filenames from existing items in the ALFA repository
    or suggests new ones according to the Axon ontology'''
    def __init__(self, directory='/home/grg/data/ALFA_DWI'):
        from brainvisa import axon
        axon.initializeProcesses()
        import neuroHierarchy
        self.__db = neuroHierarchy.databases._databases[directory]

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
        '''Types starting with @ indicate that the corresponding files must exist (ReadDiskItems). \n
        Strings starting with # designate hard-coded filenames.
        Types starting with ! indicate that the filenames will be returned without extension'''
        j = json.load(open(jsonfile))
        args_types = {
            'ants_t1': [ '@ALFA DWI B0 Brain FSL FAST White matter', '@ALFA Denoised Nobias SPM Dilated White matter', 'ALFA ANTS Elast T1 to DWI Transformation Template Filename'],
            'ants_dwi': [ '@ALFA Denoised Nobias SPM Dilated White matter', '@ALFA DWI B0 Brain FSL FAST White matter', 'ALFA ANTS Elast DWI to T1 Transformation Template Filename'],
            'ants_aal': [ '@ALFA Denoised Nobias T1 Image', '#/home/grg/data/templates/MNI_atlas_templates/MNI_T1.nii', 'ALFA ANTS SyN MNI to T1 Transformation Template Filename'],
            'warp': [ '@ALFA Denoised Nobias T1 Image', 'ALFA T1 Image Warped to DWI space', '@ALFA DWI B0 Map', '@ALFA ANTS Elast T1 to DWI Transformation', '@ALFA ANTS Elast T1 to DWI Affine Transformation'],
            'warp_md': [ '@ALFA Mean Diffusivity Image', 'ALFA DWI MD Map Warped to T1 space', '@ALFA Denoised Nobias T1 Image', '@ALFA ANTS Elast DWI to T1 Transformation', '@ALFA ANTS Elast DWI to T1 Affine Transformation'],
            'warp_md2MNI': [ '@ALFA DWI MD Map Warped to T1 space', 'ALFA DWI MD Map Warped to MNI space', '#/home/grg/data/templates/MNI_atlas_templates/MNI_T1.nii', '@ALFA ANTS SyN MNI to T1 Affine Transformation', '@ALFA ANTS SyN MNI to T1 Inverse Transformation'],
            'warp_AAL': ['#/home/grg/data/templates/MNI_atlas_templates/aal_MNI_V4.nii', 'ALFA AAL Atlas Warped to T1 space', 'ALFA Denoised Nobias T1 Image', '@ALFA ANTS SyN MNI to T1 Transformation', '@ALFA ANTS SyN MNI to T1 Affine Transformation'],
            'warp_AAL2DWI': ['@ALFA AAL Atlas Warped to T1 space', 'ALFA AAL Atlas Warped to DWI space', '@ALFA DWI B0 Map', '@ALFA ANTS Elast T1 to DWI Transformation', '@ALFA ANTS Elast T1 to DWI Affine Transformation'],
            'dtifit': ['@ALFA Denoised Corrected DWI Image', 'ALFA DWI FSL DTIFIT Template Filename', '@ALFA DWI B0 FSL Brain Mask', '@Motion-corrected Bvec File', '@Raw Bval File'],
            'eddycorrect' : ['@ALFA Denoised LPCA DWI Image', 'ALFA Denoised Corrected DWI Image'],
            'extractb0': ['@ALFA Denoised Corrected DWI Image', 'ALFA DWI B0 Map'],
            'fslbet.25' : ['@ALFA DWI B0 Map', 'ALFA DWI B0 FSL Masked Brain'],
            'fslfast': ['!ALFA DWI B0 FSL Masked Brain','ALFA DWI B0 FSL Masked Brain'],
            'rotcorr': ['@Raw Bvec File', 'Motion-corrected Bvec File', '@FSL Eddy current Correction Logfile'],
            'roistats': ['@ALFA AAL Atlas Warped to DWI space', '@ALFA Mean Diffusivity Image', 'ALFA Mean Diffusivity (AAL) ROI stats'],
            'denoising': ['@ALFA DWI Raw Image']
                }
        types = args_types[name]
        dsk = []
        for each in types:
            t = each.strip('@#!')
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
                        raise Exception('%s not found (type %s) while declared as input (or remove the leading @)'%(d, t))
                if each.startswith('!'):
                    d = self.find_diskitem(subject, t, fmt=fmt).fullPath()
                    d = d[:d.index('.')]
            dsk.append(d)
        res = parse_command(j[name], dsk)

        return res




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



