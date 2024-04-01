from argparse import ArgumentParser
from pathlib import Path

from pandas import DataFrame, Series

from rwdsim.cfgutils import SimParams, read_config
from rwdsim.simulation import run_simulation

arg_parser: ArgumentParser = ArgumentParser(description='Simulate a cohort and save results to a csv file')

arg_parser.add_argument('simconfig', type=Path, help='path to the configuration file')
arg_parser.add_argument('output', type=Path, help='path to the output csv file')

args = arg_parser.parse_args()

sim_params: SimParams
with open(args.simconfig) as cfg_file:
    sim_params = read_config(cfg_file)

data: DataFrame | Series = run_simulation(sim_params)

print(f'Saving output to {args.output}')
with open(args.output, 'w') as out_file:
    data.to_csv(out_file)
