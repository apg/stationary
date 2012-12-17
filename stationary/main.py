import sys

from stationary.config import read_config, parser
from stationary.action import TASKS

def main():
    """Do the right thing.
    """
    tasks = []
    config = read_config()

    options, args = parser.parse_args()

    for i, arg in enumerate(args):
        if arg.startswith('-'):
            break
        elif arg == 'help':
            # check for help on the *next* argument
            if (i+1) < len(pargs):
                TASKS['help']['command'](config, pargs[i+1])
            else:
                TASKS['help']['command'](config)
            raise SystemExit()
        elif arg in TASKS:
            tasks.append(TASKS[arg])
    
    for task in sorted(tasks, key=lambda x: x['priority']):
        task['command'](config)
