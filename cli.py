import argparse
from models import create_db
from utils import draw_db

from simulate import seed, generate_pvs

commands = {
    'create_db': lambda args: create_db(),
    'create_game': lambda args: game_static(args),
    'seed_pvs': lambda args: generate_pvs(),
    'draw_db': lambda args: draw_db()
}

parser = argparse.ArgumentParser(description='Media Analytics Simulation Game Helper')
parser.add_argument('command', help='Command to execute', choices=commands.keys())

args = parser.parse_args()
if not args.command in commands:
    print(f'Invalid command {args.command}')
    exit(1)

commands[args.command](args)