import argparse
from models import create_db

from simulate import seed, generate_pvs

commands = {
    'create_db': lambda args: create_db(),
    'seed_db': lambda args: seed(),
    'seed_pvs': lambda args: generate_pvs()
}

parser = argparse.ArgumentParser(description='Media Analytics Simulation Game Helper')
parser.add_argument('command', help='Command to execute', choices=commands.keys())

args = parser.parse_args()
if not args.command in commands:
    print(f'Invalid command {args.command}')
    exit(1)

commands[args.command](args)