from datetime import date, timedelta
from typing import cast

from numpy import NAN
from pandas import DataFrame, Series

from .classes import Drug, Report


def generate_report_for_drugs(data: DataFrame, report_date: date, drugs: list[Drug], report_name: str) -> Report:
    num_patients = get_num_patients(data, report_date, drugs)
    return Report(
        name=report_name,
        num_patients=num_patients,
        dx_db_delta_days=round(
            get_avg_delta_time(
                data,
                report_date,
                drugs,
                'diagnosis_date',
                'diagnosis_date_exported',
            ),
            2,
        ),
        tx_db_delta_days=round(
            get_avg_delta_time(
                data,
                report_date,
                drugs,
                'drug_date',
                'drug_date_exported',
            ),
            2,
        ),
        tx_abst_delta_days=round(
            get_avg_delta_time(
                data,
                report_date,
                drugs,
                'drug_date',
                'drug_date_abstracted',
            ),
            2,
        ),
        db_abst_delta_days=round(
            get_avg_delta_time(
                data,
                report_date,
                drugs,
                'drug_date_exported',
                'drug_date_abstracted',
            ),
            2,
        ),
        treated_fraction=round(get_treated(data, report_date, drugs) / num_patients, 2) if num_patients != 0 else NAN,
        survival_fraction=round((num_patients - get_deaths(data, report_date, drugs)) / num_patients, 2)
        if num_patients != 0
        else NAN,
    )


def get_num_patients(data: DataFrame, report_date: date, drugs: list[Drug]) -> int:
    selected_drugs = data['drug'].isin(drugs)  # pyright: ignore [reportUnknownMemberType]
    diag_date_abstracted = data['diagnosis_date_abstracted'] < report_date
    return len(data[selected_drugs & diag_date_abstracted])


def get_treated(data: DataFrame, report_date: date, drugs: list[Drug]) -> int:
    selected_drugs = data['drug'].isin(drugs)  # pyright: ignore [reportUnknownMemberType]
    drug_abstracted = data['drug_date_abstracted'] < report_date

    return len(data[selected_drugs & drug_abstracted])


def get_untreated(data: DataFrame, report_date: date) -> int:
    diag_date_abstracted = data['diagnosis_date_abstracted'] < report_date
    drug_abstracted = data['drug_date_abstracted'] < report_date

    return len(data.loc[diag_date_abstracted & ~drug_abstracted])


def get_deaths(data: DataFrame, report_date: date, drugs: list[Drug]) -> int:
    selected_drugs = data['drug'].isin(drugs)  # pyright: ignore [reportUnknownMemberType]
    diag_date_abstracted = data['diagnosis_date_abstracted'] < report_date
    death_date_abstracted = data['death_date_abstracted'] < report_date

    return len(data.loc[selected_drugs & diag_date_abstracted & death_date_abstracted])


def get_avg_delta_time(data: DataFrame, report_date: date, drugs: list[Drug], event_a: str, event_b: str) -> float:
    selected_drugs = data['drug'].isin(drugs)  # pyright: ignore [reportUnknownMemberType]
    event_a_avaliable = data[event_a] < report_date
    event_b_avaliable = data[event_b] < report_date
    valid_data = data[selected_drugs & event_a_avaliable & event_b_avaliable]
    delta_dates: Series[timedelta] = valid_data[event_b] - valid_data[event_a]
    delta_days: Series[float] = cast(Series, delta_dates / timedelta(days=1))  # pyright: ignore [reportOperatorIssue]
    return delta_days.mean()  # pyright: ignore [reportUnknownMemberType]
