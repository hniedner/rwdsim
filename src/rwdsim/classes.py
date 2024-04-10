from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from pydantic import BaseModel
from pydantic_settings import BaseSettings


class Drug(BaseModel, extra='forbid', frozen=True):
    name: str
    survival_probabilities: dict[int, float]
    start_date_range: tuple[int, int]
    probability_weights: tuple[int, ...]


@dataclass
class Patient:
    patient_id: int
    drug: Drug

    diagnosis_date: date
    diagnosis_date_exported: date | None
    diagnosis_date_abstracted: date | None

    drug_date: date | None
    drug_date_exported: date | None
    drug_date_abstracted: date | None

    death_date: date | None
    death_date_recorded: date | None
    death_date_exported: date | None
    death_date_abstracted: date | None


@dataclass
class Report:
    name: str
    num_patients: int
    dx_db_delta_days: float
    tx_db_delta_days: float
    tx_abst_delta_days: float
    db_abst_delta_days: float
    treated_drug_fraction: float
    treated_total_fraction: float
    survival_fraction: float

    def data_equals(self, other: 'Report | None') -> bool:
        if other is None:
            return False

        _name = self.name
        _other_name = other.name
        self.name = ''
        other.name = ''

        eq: bool = self == other

        self.name = _name
        other.name = _other_name

        return eq


class SimParams(BaseSettings):
    observation_start_date: date
    observation_end_date: date
    study_start_date: date
    cohort_size: int
    db_update_frequency_in_months: int
    death_date_recording_latency_range: tuple[int, int]
    patients_abstracted_per_month: int
    diagnosis_date_abstraction_latency_range: tuple[int, int]
    drug_date_abstraction_latency_range: tuple[int, int]
    death_date_abstraction_latency_range: tuple[int, int]
    drugs: tuple[Drug, ...]


class InfoStage(StrEnum):
    OCCURRED = ''
    RECORDED = '_recorded'
    EXPORTED = '_exported'
    ABSTRACTED = '_abstracted'
