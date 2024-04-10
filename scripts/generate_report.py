from argparse import ArgumentParser
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from pandas import DataFrame, Timestamp

from rwdsim.cfgutils import SimParams, read_config
from rwdsim.classes import Patient, Report
from rwdsim.reportutils import generate_report_for_drugs
from rwdsim.simulation import run_simulation

arg_parser: ArgumentParser = ArgumentParser(
    description='Simulate or load a cohort from csv and generate reports for a specified timespan'
)

arg_parser.add_argument('simconfig', type=Path, help='path to the simulator configuration file')
arg_parser.add_argument(
    '--cohort', type=Path, help='path to the cohort csv file to use instead of runnning a new simulation'
)
arg_parser.add_argument('output', type=Path, help='path to the output csv file')
arg_parser.add_argument('frequency', type=int, help='the report frequency in days')
arg_parser.add_argument(
    '--report-count',
    type=int,
    dest='report_count',
    help='the number of reports to generate per drug, will generate untill no change if left unset',
)

args = arg_parser.parse_args()
with open(args.simconfig) as cfg_file:
    sim_params: SimParams = read_config(cfg_file)

data: DataFrame

if args.cohort:
    data = pd.read_csv(  # pyright: ignore [reportUnknownMemberType]
        args.cohort,
        parse_dates=[
            key for key in Patient.__annotations__ if Patient.__annotations__[key] in [Timestamp, Timestamp | None]
        ],
        date_format='%Y-%m-%d',
    )
else:
    data = run_simulation(sim_params)

# the output reports
reports: list[Report] = []

# whole cohort
print('Generating report for whole cohort')
reports.append(
    generate_report_for_drugs(
        data,
        sim_params.study_start_date + timedelta(days=7 * 52 * 15),
        {drug.name for drug in sim_params.drugs},
        'Whole Cohort',
    )
)

# summary for each drug
for drug in sim_params.drugs:
    print(f'Generating report for {drug.name}')
    reports.append(
        generate_report_for_drugs(
            data,
            sim_params.study_start_date + timedelta(days=7 * 52 * 15),
            {
                drug.name,
            },
            drug.name,
        )
    )

# yearly reports per drug
for drug in sim_params.drugs:
    last_report: Report | None = None
    report_date: date = sim_params.study_start_date
    report_count: int = 0
    report = generate_report_for_drugs(data, report_date, {drug.name}, f'{drug.name}: {report_date}')
    while (
        args.report_count
        and report_count < args.report_count
        or not args.report_count
        and not report.data_equals(last_report)
    ):
        print(f'Generating report for {drug.name}, on {report_date}')
        reports.append(report)
        last_report = report
        report_date += timedelta(days=args.frequency)
        report_count += 1
        report = generate_report_for_drugs(data, report_date, {drug.name}, f'{drug.name}: {report_date}')

reports_df: DataFrame = DataFrame(reports)
reports_df.to_csv(args.output, index=False)
