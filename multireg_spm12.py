#!/usr/bin/env python
import nipype
from builtins import range
import argparse
import textwrap
try:
    import nipype.interfaces.io as nio           # Data i/o
    import nipype.interfaces.spm as spm          # spm
    import nipype.interfaces.fsl as fsl          # fsl
    import nipype.interfaces.matlab as mlab      # how to run matlab
    import nipype.interfaces.fsl as fsl          # fsl
    import nipype.interfaces.utility as util     # utility
    import nipype.pipeline.engine as pe          # pypeline engine
    import nipype.algorithms.modelgen as model   # model specification
    from nipype.interfaces.matlab import MatlabCommand
    from nipype.interfaces import spm
    from nipype.interfaces.spm.model import MultipleRegressionDesign
    import pandas as pd
    import os.path as osp
    import os
    from glob import glob

except ImportError:
    raise ImportError('Did you activate jupyter virtualenv (nipype) ?')

MatlabCommand.set_default_paths('/usr/local/MATLAB/R2014a/toolbox/spm12')
MatlabCommand.set_default_matlab_cmd('matlab -nodesktop -nosplash')


def run_analysis(param, excel_file, destdir, explicitmask):
    ''' Runs the analysis over a given type of parametric maps (param),
    using data from an Excel sheet as regressors (columns in 'names')
    and a given explicit mask.

    The whole analysis will be performed in the directory 'destdir'.'''

    data = pd.read_excel(excel_file)

    names = ['Apoe2-3', 'Apoe2-4', 'Apoe3-3', 'Apoe3-4', 'Apoe4-4',
                    'age23', 'age24', 'age33', 'age34', 'age44',
                    'agesq23', 'agesq24', 'agesq33', 'agesq34', 'agesq44',
                    'Gender(0=female)', 'Years of Education']
    print 'Columns used in the model:', names

    # Model Design
    vectors = [data[each].tolist() for each in names]
    centering = [1] * len(names)
    scans = data[param].tolist()
    print 'Scans (%s):'%len(scans), scans
    covariates = []
    for name, v, c in zip(names, vectors, centering):
        covariates.append(dict(name=name, centering=c, vector=v))

    model = MultipleRegressionDesign(in_files = scans,
                                    user_covariates = covariates,
                                    explicit_mask_file = explicitmask)

    # Model Estimation
    est = spm.EstimateModel(estimation_method = {'Classical': 1})

    # Contrast Estimation
    cont1 = ('Apo2-3>Apo2-4', 'T', ['Apoe2-3', 'Apoe2-4'], [1,-1])
    cont2 = ('Apo2-4>Apo3-3', 'T', ['Apoe2-4', 'Apoe3-3'], [1,-1])
    cont3 = ('Apo3-3>Apo3-4', 'T', ['Apoe3-3', 'Apoe3-4'], [1,-1])
    cont4 = ('Apo3-4>Apo4-4', 'T', ['Apoe3-4', 'Apoe4-4'], [1,-1])
    cont5 = ('Main effect ApoE', 'F', [cont1, cont2, cont3, cont4])
    cont6 = ('C<NC', 'T', ['Apoe2-3', 'Apoe2-4', 'Apoe3-3', 'Apoe3-4', 'Apoe4-4'], [3, -2, 3, -2, -2])
    cont7 = ('C>NC', 'T', ['Apoe2-3', 'Apoe2-4', 'Apoe3-3', 'Apoe3-4', 'Apoe4-4'], [-3, 2, -3, 2, 2])
    cont8 = ('HO<HZ', 'T', ['Apoe2-3', 'Apoe2-4', 'Apoe3-3', 'Apoe3-4', 'Apoe4-4'], [1, 1, 1, 1, -4])
    cont9 = ('HO>HZ', 'T', ['Apoe2-3', 'Apoe2-4', 'Apoe3-3', 'Apoe3-4', 'Apoe4-4'], [-1, -1, -1, -1, 4])
    cont10 = ('HO<All_Age_Squared', 'T', ['agesq23', 'agesq24', 'agesq33', 'agesq34', 'agesq44'], [3, -2, 3, -2, -2])
    cont11 = ('HO>All_Age_Squared', 'T', ['agesq23', 'agesq24', 'agesq33', 'agesq34', 'agesq44'], [-3, 2, -3, 2, 2])
    contrasts = [cont1, cont2, cont3, cont4, cont5, cont6, cont7, cont8, cont9, cont10, cont11]
    con = spm.EstimateContrast(contrasts = contrasts,
                               group_contrast = True)

    # Creating Workflow
    a = pe.Workflow(name='analysis')
    a.base_dir = destdir

    n1 = pe.Node(model, name='modeldesign')
    n2 = pe.Node(est, name='estimatemodel')
    n3 = pe.Node(con, name='estimatecontrasts')

    a.connect([(n1, n2, [('spm_mat_file','spm_mat_file')] ),
               (n2,n3, [('spm_mat_file', 'spm_mat_file'),
                        ('beta_images', 'beta_images'),
                        ('residual_image', 'residual_image')]), ])
    a.config['execution']['stop_on_first_rerun'] = True
    a.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
	    description=textwrap.dedent('''\
                    Runs an SPM multiple regression full analysis using data from a given table as regressors,
                    using a given explicit mask and writes the results in a given directory.
	    '''))

    parser.add_argument("param", type=str, help='Type of parametric maps to run the analysis on')
    parser.add_argument("excel", type=str, help='Excel file containing the model data')
    parser.add_argument("destdir", type=str, help='Destination directory')
    parser.add_argument("--mask", type=str, help='Explicit mask used in the analysis', required=False, default='/home/grg/spm/MNI_T1_brain_mask.nii')

    parser.add_argument("-v", dest='verbose', action='store_true', required=False, default=True)
    args = parser.parse_args()

    param = args.param
    excel = args.excel
    mask = args.mask
    destdir = args.destdir

    run_analysis(param, excel, destdir, mask)
