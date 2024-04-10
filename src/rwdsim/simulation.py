import random
from datetime import date, timedelta
from functools import cache

from dateutil.relativedelta import relativedelta
from numpy import isnan
from pandas import DataFrame
from scipy.interpolate import PchipInterpolator

from rwdsim import simutils
from rwdsim.cfgutils import SimParams

from .classes import Patient


def calculate_min_max_event_date(patients: list[Patient], event_name: str) -> tuple[date | None, date | None]:
    """
    Determines the minimum and maximum event date for any event across all patients.

    Args:
        patients (List[Patient]): The list of patients.
        event_name (str): The name of the event to check.

    Returns:
        tuple[date | None, date | None]: The earliest and latest event dates found,
                                         or None if no events of that type exist.
    """
    event_dates: list[date] = [
        getattr(patient, event_name) for patient in patients if getattr(patient, event_name) is not None
    ]

    if not event_dates:  # If there are no event dates, return None for both min and max
        return None, None

    return min(event_dates), max(event_dates)


def calculate_next_abstraction_assessment_date(offset_date: date, sim_params: SimParams) -> date:
    """
    Calculates the next abstraction assessment date based on the offset date and the database update frequency.

    Args:
        offset_date (date): The offset date.
        sim_params (SimParams): The simulation parameters.

    Returns:
        date: The next abstraction assessment date.
    """
    return offset_date + relativedelta(months=sim_params.db_update_frequency_in_months, day=2)


def determine_treatment_date(
    diagnosis_date: date,
    death_date: date | None,
    treatment_date_range: tuple[int, int],
) -> date | None:
    """Determines the treatment date for a given patient.

    Args:
        diagnosis_date (date): The patient's diagnosis date.
        death_date (date): The patient's death date.
        treatment_fraction_range (tuple[float, float]): The range of treatment fractions.
        treatment_date_range (tuple[int, int]): The range of treatment dates.

    Returns:
        date: The treatment date.
    """
    # Generate a random treatment date offset from the diagnosis date in days
    treatment_date_offset: int = random.randint(*treatment_date_range)
    # Generate a random treatment date
    treatment_date: date = diagnosis_date + timedelta(days=treatment_date_offset)
    # Ensure that the treatment date is not after the death date
    if death_date is None or treatment_date < death_date:
        return treatment_date
    # Otherwise, return None - indicating that the patient does not receive treatment
    return None


def determine_death_date(diagnosis_date: date, survival_probabilities: dict[int, float]) -> date | None:
    interpolated = _get_interpolator(tuple(survival_probabilities.keys()), tuple(survival_probabilities.values()))
    year_delta: float = interpolated([random.random()])[0]
    if isnan(year_delta):
        return None

    return diagnosis_date + timedelta(days=year_delta * 365.25)


@cache
def _get_interpolator(survival_years: tuple[int, ...], survival_probabilities: tuple[float, ...]) -> PchipInterpolator:
    x = [1.0]
    x.extend(survival_probabilities)
    y = [0]
    y.extend(survival_years)
    return PchipInterpolator(x[::-1], y[::-1], extrapolate=False)


def simulate_delayed_recording_date(event_date: date | None, latency_range: tuple[int, int]) -> date | None:
    """
    Simulates the delayed recording date for a given event date.

    Args:
        event_date (date): The event date.
        latency_range (tuple[int, int]): The range of latencies in days.

    Returns:
        date: The delayed recording date.
    """
    if event_date is None:
        return None
    latency_days = random.randint(*latency_range)
    return event_date + timedelta(days=latency_days)


def calculate_exported_date(
    event_date: date | None, study_start_date: date, db_update_frequency_in_months: int
) -> date | None:
    """
    Calculates the date when the data would be exported to the database for a given event date.
    The data is exported to the database on a x-monthly basis (default is monthly on the first day of the month).

    Args:
        event_date (date): The date when the event was recorded in the EHR.
        study_start_date (date): The date when the study began.
        db_update_frequency_in_months (int): The frequency, in months, at which the database is updated.

    Returns:
        date: The date when the data would be exported to the database.
    """
    if not event_date:
        return None

    if event_date < study_start_date:
        # If the event date is before the study start date, set the export date
        # to the first export cycle after the study start date
        return study_start_date.replace(day=1) + relativedelta(months=db_update_frequency_in_months)

    # Calculate the time difference from the event date to the study start date
    months_since_study_start = (
        (event_date.year - study_start_date.year) * 12 + event_date.month - study_start_date.month
    )

    # Find out how many months until the next export cycle
    months_since_last_export = months_since_study_start % db_update_frequency_in_months
    months_until_next_export = db_update_frequency_in_months - months_since_last_export

    if months_since_last_export == 0:
        # If the event happens to fall exactly on an export cycle, set the next export to the next cycle
        months_until_next_export = db_update_frequency_in_months

    # Calculate the next export date
    next_export_date = event_date + relativedelta(months=months_until_next_export)
    # Set the day to the first of the month
    return next_export_date.replace(day=1)


def is_event_exported(event_date: date | None, event_date_exported: date | None, export_date: date) -> bool:
    """
    Determines whether an event is exported by the given export date.
    On the given export date, the event is considered to be exported
     * if the event date (or event date recorded for death_date), is not None since there is nothing to export;
     * if the event export date is not None, since it had already been exported on that date;
     * if the event export date is after the export date, since it has not occurred yet;

    Args:
        event_date (date): The date when the event occurred.
        event_date_exported (date): The date when the event was exported.
        export_date (date): The date when the data are being assessed for export.

    Returns:
        bool: Whether the event is exported.
    """
    # If the event hasn't occurred, it's considered exported
    if event_date is None:
        return True

    # If the event occurred but hasn't been exported, it's not exported
    if event_date_exported is None:
        return False

    # If the event has been exported before or on the export date, it's exported
    return event_date_exported <= export_date


def is_patient_fully_exported(patient: Patient, export_date: date) -> bool:
    """
    Determines whether a patient is fully exported.
    A patient is fully exported if all of its events are considered to be exported on the given export date.

    Args:
        patient (Patient): The patient.
        export_date (date): The date when the data are being exported to the database.

    Returns:
        bool: Whether the patient is fully exported.
    """
    event_pairs: list[tuple[date | None, date | None]] = [
        (patient.diagnosis_date, patient.diagnosis_date_exported),
        (patient.drug_date, patient.drug_date_exported),
        (patient.drug_date, patient.drug_date_exported),
        (patient.death_date_recorded, patient.death_date_exported),
    ]
    return all(
        is_event_exported(event_date, event_date_exported, export_date)
        for event_date, event_date_exported in event_pairs
    )


def generate_patient_cohort(sim_params: SimParams) -> list[Patient]:
    """
    Generates a cohort of patients with simulated diagnosis, treatment, and death dates.

    Args:
    sim_params (SimParams): The simulation parameters.

    Returns:
    List[Patient]: A list of patient records.
    """
    cohort: list[Patient] = []
    for patient_id in range(1, sim_params.cohort_size + 1):
        # Generate a random diagnosis date
        diagnosis_date = simutils.generate_random_date(
            sim_params.observation_start_date, sim_params.observation_end_date
        )
        # Select a random drug from those configured  TODO: different likelyhoods for each drug
        drug = simutils.select_drug(
            diagnosis_date, sim_params.drugs, sim_params.observation_start_date, sim_params.observation_end_date
        )
        # Generate a random death date
        death_date = determine_death_date(diagnosis_date, drug.survival_probabilities)
        # Generate death date recorded date with a random delay within the range of the death date recording latency
        death_date_recorded = (
            simulate_delayed_recording_date(death_date, sim_params.death_date_recording_latency_range)
            if death_date
            else None
        )
        # Generate a random treatment date
        drug_date = determine_treatment_date(
            diagnosis_date,
            death_date,
            drug.start_date_range,
        )
        # Create a patient record and add it to the cohort
        cohort.append(
            Patient(
                patient_id=patient_id,
                drug=drug,
                diagnosis_date=diagnosis_date,
                drug_date=drug_date,
                death_date=death_date,
                death_date_recorded=death_date_recorded,
                diagnosis_date_exported=None,
                drug_date_exported=None,
                death_date_exported=None,
                diagnosis_date_abstracted=None,
                drug_date_abstracted=None,
                death_date_abstracted=None,
            )
        )
    return cohort


def generate_exported_dates(patients: list[Patient], sim_params: SimParams) -> None:
    """
    Iterates over the patients and assigns exported dates to the events that have not been exported yet.

    Args:
        patients (List[Patient]): The list of patients to process.
        sim_params (SimParams): The simulation parameters.
    """
    for patient in patients:
        for event_name in [
            'diagnosis_date',
            'drug_date',
            'death_date_recorded',
        ]:
            # For death_date, we use death_date_recorded as the event date
            event_date: date | None = getattr(patient, event_name)

            # remove the _recorded suffix from the death_date and
            # append _exported to create the exported date attribute name
            exported_date_attr: str = f"{event_name.replace('_recorded', '')}_exported"

            # Set the exported date attribute to the calculated exported date
            setattr(
                patient,
                exported_date_attr,
                calculate_exported_date(
                    event_date=event_date,
                    db_update_frequency_in_months=sim_params.db_update_frequency_in_months,
                    study_start_date=sim_params.study_start_date,
                ),
            )


def is_event_abstractable(
    event_date_exported: date | None,
    event_date_abstracted: date | None,
    assessment_date: date,
) -> bool:
    """
    Determines whether an event is ready for abstraction based on its export and abstraction status.

    An event is ready for abstraction if it has been exported to the database by the assessment date
    and has not yet been abstracted by the assessment date.

    Args:
        event_date_exported: The date when the event was exported to the database.
        event_date_abstracted: The date when the event was last abstracted.
        assessment_date: The date when the data is being assessed for abstraction.

    Returns:
        bool: True if the event is ready for abstraction, False otherwise.
    """
    is_abstractable: bool = True
    # If the event has already been abstracted or has not been exported, it's not ready for abstraction
    if event_date_abstracted is not None:
        is_abstractable = False
    # If the event has not been exported or has been exported after the assessment date, it's not ready for abstraction
    if event_date_exported is None or event_date_exported > assessment_date:
        is_abstractable = False
    # In any other case, the event is not ready for abstraction
    return is_abstractable


def is_patient_abstractable(patient: Patient, assessment_date: date) -> bool:
    """
    Determines whether any event of a patient is ready for abstraction.

    Args:
        patient: The patient object containing event dates and their exported/abstracted status.
        assessment_date: The date when the data is being assessed for abstraction.

    Returns:
        bool: True if any event of the patient is ready for abstraction, False otherwise.
    """
    # Return True if any event of the patient is ready for abstraction
    return any(
        # Check each event in the patient record to see if it's ready for abstraction
        is_event_abstractable(
            event_date_exported=getattr(patient, f'{event}_date_exported'),
            event_date_abstracted=getattr(patient, f'{event}_date_abstracted'),
            assessment_date=assessment_date,
        )
        # Iterate over the patient events
        for event in ['diagnosis', 'drug', 'death']
    )


def is_patient_fully_abstracted(patient: Patient) -> bool:
    """
    Determines whether a patient is fully abstracted.
    A patient is fully abstracted if all of its events are considered to be abstracted.
    That means all not None events are exported and abstracted.

    Args:
        patient (Patient): The patient.

    Returns:
        bool: Whether the patient is fully abstracted.
    """
    is_fully_abstracted: bool = True
    # Checking each event in the patient record
    events: list[tuple[date | None, date | None]] = [
        (patient.diagnosis_date, patient.diagnosis_date_abstracted),
        (patient.drug_date, patient.drug_date_abstracted),
        (patient.drug_date, patient.drug_date_abstracted),
        (patient.death_date, patient.death_date_abstracted),
    ]
    # Iterating over each event in the patient record and checking if it's abstracted.
    for event_date, event_date_abstracted in events:
        # If the event date is not None, check if it's exported and abstracted
        if event_date is not None and event_date_abstracted is None:
            # If the event did occur but was not abstracted, set is_fully_abstracted to False
            is_fully_abstracted = False

    # If all not None events are abstracted, return True.
    return is_fully_abstracted


def set_events_abstracted_date(
    sim_params: SimParams,
    patient: Patient,
    event_name: str,
    assessment_date: date,
) -> None:
    event_exported_name = f'{event_name}_date_exported'
    event_abstracted_name = f'{event_name}_date_abstracted'
    event_exported_date: date = getattr(patient, event_exported_name)
    abstracted_date: date = getattr(patient, event_abstracted_name)
    # Check if the event can be abstracted.
    # An event can be abstracted if it has been exported before the assessment date
    # and the event's abstraction date is not set yet.
    if is_event_abstractable(
        event_date_exported=event_exported_date,
        event_date_abstracted=abstracted_date,
        assessment_date=assessment_date,
    ):
        # Calculate the abstracted date based on the event's abstraction latency range
        latency_range = getattr(sim_params, f'{event_name}_date_abstraction_latency_range')
        abstraction_latency = random.randint(*latency_range)
        abstracted_date = event_exported_date + timedelta(days=abstraction_latency)

        # Update the patient record
        setattr(patient, event_abstracted_name, abstracted_date)


def generate_abstracted_dates(patients: list[Patient], sim_params: SimParams) -> None:
    """
    Iterates over the patients and assigns abstracted dates to the events that have been exported but not yet
    abstracted.

    Args:
        patients (List[Patient]): The list of patients to process.
        sim_params (SimParams): The simulation parameters.
    """

    # Initialize the assessment_date
    assessment_date: date = calculate_next_abstraction_assessment_date(
        offset_date=sim_params.study_start_date,
        sim_params=sim_params,
    )

    while True:
        # Determine patients with events that can be abstracted at the current assessment_date
        abstractable_patients = [patient for patient in patients if is_patient_abstractable(patient, assessment_date)]

        if not abstractable_patients:
            break  # Exit the loop if there are no abstractable patients

        # Select patients to abstract
        patients_to_abstract = random.sample(
            abstractable_patients,
            # Limit the number of patients to abstract to the number of patients
            # that can be abstracted per db updates frequency (nr of months)
            # and abstraction rate (number of patients per month)
            min(
                sim_params.patients_abstracted_per_month * sim_params.db_update_frequency_in_months,
                len(abstractable_patients),
            ),
        )

        # Assign abstracted dates to the selected patients' events
        for patient in patients_to_abstract:
            for event_name in ['diagnosis', 'drug', 'death']:
                set_events_abstracted_date(
                    sim_params=sim_params,
                    patient=patient,
                    event_name=event_name,
                    assessment_date=assessment_date,
                )

        # Move to the next month and update the assessment date
        assessment_date = calculate_next_abstraction_assessment_date(
            offset_date=assessment_date,
            sim_params=sim_params,
        )

        # Check if all patients are fully abstracted; if so, break the loop
        if all(is_patient_fully_abstracted(patient) for patient in patients):
            break


def sanity_check_patient_records(patients: list[Patient]) -> None:
    """
    Sanity checks the patient records.
    Checks if the patient records are consistent. For each patient, it checks:
    - If the diagnosis date is set.
    - If the exported dates are set after the event dates.
    - If the abstracted dates are set after the exported dates.
    - If the death date is recorded and recorded correctly.

    Args:
        patients (List[Patient]): The list of patients to check.

    Raises:
        Exception: If the patient records are inconsistent.
    """
    for patient in patients:
        if patient.diagnosis_date is None:
            raise Exception(f'Diagnosis date is not set for patient {patient.patient_id}')

        if patient.death_date and (
            patient.death_date_recorded is None or patient.death_date > patient.death_date_recorded
        ):
            raise Exception(f'Death date is recorded incorrectly for patient {patient.patient_id}')

        for event in ['diagnosis', 'drug', 'death']:
            event_date: date | None = getattr(patient, f'{event}_date')
            event_date_exported: date | None = getattr(patient, f'{event}_date_exported')
            event_date_abstracted: date | None = getattr(patient, f'{event}_date_abstracted')

            if event_date and event_date_exported and event_date > event_date_exported:
                raise Exception(f'{event.capitalize()} date is after its export date for patient {patient.patient_id}')

            if event_date_exported and event_date_abstracted and event_date_exported > event_date_abstracted:
                raise Exception(
                    f'{event.capitalize()} export date is after its abstraction date for patient {patient.patient_id}'
                )

            if event_date and event_date_abstracted and event_date > event_date_abstracted:
                raise Exception(
                    f'{event.capitalize()} date is after its abstraction date for patient {patient.patient_id}'
                )


def run_simulation(simulation_params: SimParams) -> DataFrame:
    print('##########################################################################')
    print('#  Simulation parameters:                                               #')
    print('##########################################################################')
    print('\n'.join(f'{key}: {value}' for key, value in simulation_params.model_dump().items()))
    print('##########################################################################')
    print()
    # Generate patient data
    cohort: list[Patient] = generate_patient_cohort(simulation_params)
    print(f'Generated patient cohort for {len(cohort)} patients.')

    # Assign export dates to the events of the patients
    generate_exported_dates(patients=cohort, sim_params=simulation_params)
    print(f'Generated export dates for {len(cohort)} patients.')

    # Assign abstracted dates to the events of the patients
    generate_abstracted_dates(patients=cohort, sim_params=simulation_params)
    # Filter patients who are fully abstracted now at the assessment date.
    fully_abstracted_patients: list[Patient] = [patient for patient in cohort if is_patient_fully_abstracted(patient)]
    print(f'Fully abstracted {len(fully_abstracted_patients)} patients.')

    try:
        sanity_check_patient_records(cohort)
        print(f'{len(cohort)} patient records passed the sanity check.')
    except Exception as e:
        print(e, type(e))

    print('Cohort Stats:')
    print(f'Study start date: {simulation_params.study_start_date}')
    for event in ['diagnosis', 'drug', 'death']:
        for event_suffix in ['date', 'date_exported', 'date_abstracted']:
            event_name: str = f'{event}_{event_suffix}'
            min_date, max_date = calculate_min_max_event_date(cohort, event_name)
            print(f'{event_name} min: {min_date} and max: {max_date}.')

    # convert the patient time data to a pandas dataframe
    cohort_df: DataFrame = DataFrame(cohort)
    cohort_df = cohort_df.sort_values(by='diagnosis_date')  # pyright: ignore [reportUnknownMemberType]

    # rearrange the columns to juxtaposition the event date with the export date and the abstracted date
    cohort_df = cohort_df[
        [
            'patient_id',
            'drug',
            'diagnosis_date',
            'diagnosis_date_exported',
            'diagnosis_date_abstracted',
            'drug_date',
            'drug_date_exported',
            'drug_date_abstracted',
            'death_date',
            'death_date_recorded',
            'death_date_exported',
            'death_date_abstracted',
        ]
    ]

    return cohort_df
