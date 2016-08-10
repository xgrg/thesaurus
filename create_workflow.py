#! /usr/bin/env python
import argparse
import textwrap
import os.path as osp
from soma_workflow.client import Job, Workflow, Helper


if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
	    description=textwrap.dedent('''\
	    Creates a parallelized workflow for soma-workflow from a text file containing one-line commands
	    '''))

    parser.add_argument("-i", dest='input', type=str, required=True, help='Text file containing commands')
    parser.add_argument("-o", dest='output', type=str, required=True, help='File containing workflow')
    parser.add_argument("-v", dest='verbose', action='store_true', required=False)
    args = parser.parse_args()

    inp = args.input
    out = args.output

    if not osp.isfile(inp):
        raise Exception('File not found %s'%inp)

    commands = [e.rstrip('\n').split(' ') for e in open(inp).readlines()]
    if args.verbose:
        print commands

    jobs = [Job(command=cmd, name='job_%s'%i) for i,cmd in enumerate(commands)]
    workflow = Workflow(jobs=jobs, dependencies=[])
    Helper.serialize(out, workflow)

    if osp.isfile(out):
        print 'Workflow successfully created (%s)'%out
    else:
        raise Exception('Error in generating workflow.')
