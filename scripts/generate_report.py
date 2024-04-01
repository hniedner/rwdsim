from argparse import ArgumentParser
from pathlib import Path

import pandas as pd
from pandas import DataFrame

from rwdsim.cfgutils import SimParams, read_config
from rwdsim.simulation import run_simulation

arg_parser: ArgumentParser = ArgumentParser(
    description='Simulate or load a cohort from csv and generate reports for a specified timespan'
)

exclusive_group = arg_parser.add_mutually_exclusive_group(required=True)
exclusive_group.add_argument('--simconfig', type=Path, help='path to the simulator configuration file')
exclusive_group.add_argument('--cohort', type=Path, help='path to the cohort csv file')
arg_parser.add_argument('output', type=Path, help='path to the output csv file')

args = arg_parser.parse_args()


data: DataFrame

if args.simconfig:
    sim_params: SimParams
    with open(args.simconfig) as cfg_file:
        sim_params = read_config(cfg_file)

    data = run_simulation(sim_params)
else:
    data = pd.read_csv(args.cohort)  # pyright: ignore [reportUnknownMemberType]
