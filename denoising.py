from string import Template
import subprocess
import os.path as osp
import os

import argparse
import textwrap

def createScript(source, text):
    """Very not useful and way over simplistic method for creating a file

    Args:
        source: The absolute name of the script to create
        text: Text to write into the script

    Returns:
        True if the file have been created

    """
    try:
        with open(source, 'w') as f:
            f.write(text)
    except IOError:
        return False
    return True


def parseTemplate(dict, template):
    """provide simpler string substitutions as described in PEP 292

    Args:
       dict: dictionary-like object with keys that match the placeholders in the template
       template: object passed to the constructors template argument.

    Returns:
        the string substitute

    """
    with open(template, 'r') as f:
        return Template(f.read()).safe_substitute(dict)


def launchCommand(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=None, nice=0):
    import sys
    sys.path.append('/home/grg/toad')
    from lib import util
    """Execute a program in a new process

    Args:
	command: a string representing a unix command to execute
	stdout: this attribute is a file object that provides output from the child process
	stderr: this attribute is a file object that provides error from the child process
	timeout: Number of seconds before a process is consider inactive, usefull against deadlock
	nice: run cmd  with  an  adjusted  niceness, which affects process scheduling

    Returns
	return a 3 elements tuples representing the command execute, the standards output and the standard error message

    Raises
	OSError:      the function trying to execute a non-existent file.
	ValueError :  the command line is called with invalid arguments

    """
    binary = cmd.split(" ").pop(0)
    if util.which(binary) is None:
	print ("Command {} not found".format(binary))

    print ("Launch {} command line...".format(binary))
    print ("Command line submit: {}".format(cmd))

    (executedCmd, output, error)= util.launchCommand(cmd, stdout, stderr, timeout, nice)
    if not (output is "" or output is "None" or output is None):
	print("Output produce by {}: {} \n".format(binary, output))

    if not (error is '' or error is "None" or error is None):
	print("Error produce by {}: {}\n".format(binary, error))


def denoise(source):

    assert(osp.isfile(source))
    filename, ext = osp.splitext(source)
    print ext
    assert(ext in ['.nii', '.gz'])
    if ext == '.gz':
       print 'unzipping %s'%source
       os.system('gunzip %s'%source)
       source = filename
    target = '%s_denoised.nii'%osp.splitext(source)[0]
    print source, '->', target
    workingDir = osp.split(source)[0]
    tpl_fp = '/home/grg/denoising/denoise.tpl'
    matlab_tpl = '/home/grg/denoising/matlab.tpl'


    tags={ 'source': source,
           'target': target,
           'workingDir': workingDir,
           'beta': 1,
           'rician': 1,
           'nbthreads': 32}

    template = parseTemplate(tags, tpl_fp)

    import tempfile
    code, tmpfile = tempfile.mkstemp(suffix='.m')
    print 'creating tempfile %s'%tmpfile
    createScript(tmpfile, template)

    tmpbase = osp.splitext(tmpfile)[0]
    tags={ 'script': tmpbase, 'workingDir': workingDir}
    cmd = parseTemplate(tags, matlab_tpl)
    print cmd
    os.system(cmd)
    #launchCommand(cmd)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
            description=textwrap.dedent('''\
            Denoising using LPCA
            '''))

    parser.add_argument("-i", dest='input', type=str, required=True)
    args = parser.parse_args()
    source = args.input
    denoise(source)


