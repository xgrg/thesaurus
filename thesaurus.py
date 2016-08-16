#! /usr/bin/env python
import argparse
import textwrap
import os.path as osp
import json
import os

def parse_command(cmd, args):
    if len(a) != cmd.count('%s'):
        raise Exception('%s (%s)\n%s\n%s'%(
            args, len(args),
            j[name],
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



