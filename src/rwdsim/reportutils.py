from datetime import date, timedelta
from os import PathLike
from pathlib import Path

import pandas as pd
from pandas import DataFrame

from .cfgutils import SimParams, read_config
from .simulation import Patient


def generate_report(data: DataFrame) -> DataFrame:
    for report_date in pd.date_range(
        params.study_start_date,
        params.study_start_date + timedelta(weeks=52 * 10),
        freq='M',
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
