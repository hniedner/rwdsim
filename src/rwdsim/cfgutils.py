# Define type variables for generic type annotations
import configparser
from dataclasses import dataclass
from datetime import date, datetime
from io import TextIOWrapper
from typing import Type

iorf = int | float


def parse_dict[T1: iorf, T2: iorf](value: str, key_type: Type[T1], value_type: Type[T2]) -> dict[T1, T2]:
    """
    Parses a string in the format "key: value, key: value, .....", where key and value are separated by a colon

    Args:
        value (str): The string to parse.
        key_type (T1): The type of the keys in the dictionary. Expected to be either int or float.
        value_type (T2): The type of the values in the dictionary. Expected to be either int or float.

    Returns:
        dict[T1, T2]: A dictionary with the specified types for keys and values.
    """
    # Split the string by comma and strip whitespace
    parts = [part.strip() for part in value.split(',')]
    retval: dict[T1, T2] = {}
    for part in parts:
        # Split the part by colon and strip whitespace
        key, value = [part.strip() for part in part.split(':')]
        retval[key_type(key)] = value_type(value)

    return retval


def parse_tuple[T1: iorf, T2: iorf](value: str, type1: Type[T1], type2: Type[T2]) -> tuple[T1, T2]:
    """
    Parses a string in the format "valueA, valueB", where valueA and valueB are separated by a comma
    and may have variable whitespace around them. It returns a tuple of two values with the specified types.

    Args:
    s (str): The string to parse.
    type1 (T1): The type of the first value in the tuple. Expected to be either int or float.
    type2 (T2): The type of the second value in the tuple. Expected to be either int or float.

    Returns:
    tuple[T1, T2]: A tuple of two values with the specified types.
    """
    # Split the string by comma and strip whitespace
    parts = [part.strip() for part in value.split(',')]

    # Ensure type1 and type2 are callable
    if not (callable(type1) and callable(type2)):
        raise ValueError('type1 and type2 must be callable')

    # Convert each part to the specified type
    value1: type1 = type1(parts[0])
    value2: type2 = type2(parts[1])

    return value1, value2


def parse_dict_if(value: str) -> dict[int, float]:
    return parse_dict(value, int, float)


def parse_tuple_ii(s: str) -> tuple[int, int]:
    return parse_tuple(s, int, int)


def parse_tuple_if(s: str) -> tuple[int, float]:
    return parse_tuple(s, int, float)


def parse_tuple_ff(s: str) -> tuple[float, float]:
    return parse_tuple(s, float, float)


def parse_date(value: str) -> date:
    """
    Parses a string in the format "YYYY-MM-DD", where YYYY, MM, and DD are separated by a dash.

    Args:
        value (str): The string to parse.

    Returns:
        date: A date object with the specified year, month, and day.
    """
    return datetime.strptime(value, '%Y-%m-%d').date()


@dataclass
class SimParams:
    observation_start_date: date
    observation_end_date: date
    study_start_date: date
    cohort_size: int
    drug_a_treatment_fraction_range: tuple[float, float]
    drug_b_treatment_fraction_range: tuple[float, float]
    drug_a_start_date_range: tuple[int, int]
    drug_b_start_date_range: tuple[int, int]
    survival_probabilities_per_year: dict[int, float]
    db_update_frequency_in_months: int
    death_date_recording_latency_range: tuple[int, int]
    patients_abstracted_per_month: int
    diagnosis_date_abstraction_latency_range: tuple[int, int]
    drug_a_date_abstraction_latency_range: tuple[int, int]
    drug_b_date_abstraction_latency_range: tuple[int, int]
    death_date_abstraction_latency_range: tuple[int, int]


def read_config(config_file: TextIOWrapper) -> SimParams:
    """Reads simulation parameters from a configuration file and populates the SimParams named tuple.

    Args:
        config_file_path (str): Path to the configuration file.

    Returns:
        SimParams: A named tuple containing all simulation parameters.
    """
    config = configparser.ConfigParser(
        converters={
            '_dict_if': parse_dict_if,
            '_tuple_ii': parse_tuple_ii,
            '_tuple_if': parse_tuple_if,
            '_tuple_ff': parse_tuple_ff,
            '_date': parse_date,
        }
    )
    config.read_file(config_file)

    params = SimParams(
        observation_start_date=config.get_date('SimParams', 'observation_start_date'),  # pyright: ignore [reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownArgumentType]
        observation_end_date=config.get_date('SimParams', 'observation_end_date'),  # pyright: ignore [reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownArgumentType]
        study_start_date=config.get_date('SimParams', 'study_start_date'),  # pyright: ignore [reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownArgumentType]
        cohort_size=config.getint('SimParams', 'cohort_size'),
        drug_a_treatment_fraction_range=config.get_tuple_ff(  # pyright: ignore [reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownArgumentType]
            'SimParams', 'drug_a_treatment_fraction_range'
        ),
        drug_b_treatment_fraction_range=config.get_tuple_ff(  # pyright: ignore [reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownArgumentType]
            'SimParams', 'drug_b_treatment_fraction_range'
        ),
        drug_a_start_date_range=config.get_tuple_ii(  # pyright: ignore [reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownArgumentType]
            'SimParams', 'drug_a_start_date_range'
        ),
        drug_b_start_date_range=config.get_tuple_ii(  # pyright: ignore [reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownArgumentType]
            'SimParams', 'drug_b_start_date_range'
        ),
        survival_probabilities_per_year=config.get_dict_if(  # pyright: ignore [reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownArgumentType]
            'SimParams', 'survival_probabilities_per_year'
        ),
        db_update_frequency_in_months=config.getint('SimParams', 'db_update_frequency_in_months'),
        death_date_recording_latency_range=config.get_tuple_ii(  # pyright: ignore [reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownArgumentType]
            'SimParams', 'death_date_recording_latency_range'
        ),
        patients_abstracted_per_month=config.getint('SimParams', 'patients_abstracted_per_month'),
        diagnosis_date_abstraction_latency_range=config.get_tuple_ii(  # pyright: ignore [reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownArgumentType]
            'SimParams', 'diagnosis_date_abstraction_latency_range'
        ),
        drug_a_date_abstraction_latency_range=config.get_tuple_ii(  # pyright: ignore [reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownArgumentType]
            'SimParams', 'drug_a_date_abstraction_latency_range'
        ),
        drug_b_date_abstraction_latency_range=config.get_tuple_ii(  # pyright: ignore [reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownArgumentType]
            'SimParams', 'drug_b_date_abstraction_latency_range'
        ),
        death_date_abstraction_latency_range=config.get_tuple_ii(  # pyright: ignore [reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownArgumentType]
            'SimParams', 'death_date_abstraction_latency_range'
        ),
    )

    return params
