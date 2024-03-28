from datetime import date, timedelta
from os import PathLike
import pandas as pd
from pandas.core.api import DataFrame
from .cfgutils import read_config, SimParams
from .main import Patient


def generate_report(
    input_file: PathLike, config_file: PathLike, output_file: PathLike
) -> None:
    params: SimParams = read_config(config_file)
    data = pd.read_csv(input_file)

    for report_date in pd.date_range(
        params.study_start_date,
        params.study_start_date + timedelta(weeks=52 * 10),
        freq="M",
    ):
        generate_month_report(data, report_date)


def generate_month_report(data: pd.DataFrame, report_date: date) -> ...: ...


def get_cohort_size(data: DataFrame, report_date: date) -> int:
    col = Patient.diagnosis_date_abstracted.__qualname__
    return data[data[col] < report_date].size


def get_new_patients(data: DataFrame, report_date: date, prev_report_date: date) -> int:
    col = Patient.diagnosis_date_abstracted.__qualname__
    return data[data[col] < report_date, data[col] >= prev_report_date].size


def get_treated(data: DataFrame, report_date: date, drugs: list[str]) -> int: ...


def get_untreated(data: DataFrame, report_date: date) -> int: ...


def get_deaths(data: DataFrame, report_date: date) -> int: ...


def get_migrations(data: DataFrame, report_date: date) -> int: ...
