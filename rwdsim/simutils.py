from datetime import date
from datetime import timedelta

import numpy as np


def generate_random_date(start_date: date, end_date: date) -> date:
    """Generate a random date within the specified year.

    Args:
        start_date (int): The year to start generating random dates for.
        end_date (int): The year to stop generating random dates for.

    Returns:
        date: A random date between start_date and end_date.
    """
    return start_date + timedelta(days=np.random.randint(0, (end_date - start_date).days))


def calculate_probabilities_over_period(
        start_year: int,
        observation_period: int,
        probability_range: tuple[float, float]
) -> dict[int, float]:
    """
    Calculate varying probabilities over a specified observation period.

    This function generates a list of probabilities that either increase or decrease
    linearly from a start probability to an end probability over a given number of years,
    starting from a specified start year. Randomness is introduced in the increments
    to ensure variability, while still hitting the exact end probability.

    Parameters:
    - start_year (int): The year in which the observation period begins.
    - observation_period (int): The number of years over the observation period.
    - probability_range (float, float): The range of probabilities to generate over the period.

    Returns:
    - List of tuples: Each tuple contains a year and its corresponding probability.
    """
    start_prob: float = probability_range[0]
    end_prob: float = probability_range[1]

    if observation_period < 1:
        raise ValueError("Observation period must be at least 1 year.")

    if start_prob < 0 or start_prob > 1:
        raise ValueError("Start probability must be between 0 and 1.")

    if end_prob < 0 or end_prob > 1:
        raise ValueError("End probability must be between 0 and 1.")

    np.random.seed(42)  # Ensure reproducible results
    total_change: float = end_prob - start_prob  # Total change required over the period
    increments = np.random.rand(observation_period - 1)  # Random increments for variability
    increments *= total_change / sum(increments)  # Scale increments to sum to total change

    probabilities: list[float] = [start_prob]  # Initialize probabilities list with start probability
    for increment in increments:
        next_prob = probabilities[-1] + increment  # Calculate next probability
        probabilities.append(next_prob)

    probabilities[-1] = end_prob  # Ensure exact end probability

    # Generate and return dictionary of year: probability pairs
    return dict(zip(range(start_year, start_year + observation_period), probabilities))


def normalize_probabilities(probabilities: dict[int, float]) -> list[float]:
    """
    Normalize a dictionary of probabilities so they sum to 1.

    Parameters:
    - probabilities: A dictionary with years as keys and probabilities as values.

    Returns:
    - A list of normalized probabilities.
    """
    if len(probabilities) < 1:
        raise ValueError("Cannot normalize an empty dictionary.")
    total_prob = sum(probabilities.values())
    normalized_probs = [prob / total_prob for prob in probabilities.values()]
    return normalized_probs


def calculate_missing_probabilities(
        survival_dict: dict[int, float],
        observation_period: int
) -> dict[int, float]:
    """
    Interpolates missing probabilities for missing years and extrapolates probabilities
    if the observation period is longer than covered by the provided probabilities.

    Parameters:
    - survival_dict (Dict[int, float]): A dictionary with the number of years from diagnosis as keys and survival
    probabilities as values.
    - observation_period (int): The total observation period in years.

    Returns:
    - Dict[int, float]: A dictionary with each number of years from diagnosis up to the observation period mapped to
    the interpolated or extrapolated probabilities.
    """
    if not survival_dict:
        raise ValueError("Survival dictionary cannot be empty.")

    if observation_period < 1:
        raise ValueError("Observation period must be at least 1 year.")

    sorted_years = sorted(survival_dict.keys())
    full_range_years = range(sorted_years[0], observation_period + 1)
    interpolated_dict = {}

    for year in full_range_years:
        if year in survival_dict:
            interpolated_dict[year] = survival_dict[year]
        else:
            # Interpolate if within the range of provided years
            if year < sorted_years[-1]:
                lower_year = max([y for y in sorted_years if y < year])
                upper_year = min([y for y in sorted_years if y > year])
                # Linear interpolation
                slope = (survival_dict[upper_year] - survival_dict[lower_year]) / (upper_year - lower_year)
                interpolated_dict[year] = survival_dict[lower_year] + slope * (year - lower_year)
            # Extrapolate if beyond the range of provided years
            else:
                if len(sorted_years) >= 2:
                    # Use last two years for slope
                    last_year = sorted_years[-1]
                    second_last_year = sorted_years[-2]
                    slope = (survival_dict[last_year] - survival_dict[second_last_year]) / (
                                last_year - second_last_year)
                    extrapolated_value = survival_dict[last_year] + slope * (year - last_year)
                    interpolated_dict[year] = extrapolated_value
                else:
                    # Cannot extrapolate with less than 2 data points; use the last known value
                    interpolated_dict[year] = survival_dict[sorted_years[-1]]

    return interpolated_dict
