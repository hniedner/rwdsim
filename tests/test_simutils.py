from datetime import date

import pytest

from rwdsim.simutils import calculate_missing_probabilities
from rwdsim.simutils import calculate_probabilities_over_period
from rwdsim.simutils import generate_random_date
from rwdsim.simutils import normalize_probabilities


##############################
# generate_random_date tests #
##############################

def test_generate_random_date_return_type():
    start_date = date(2015, 1, 1)
    end_date = date(2020, 1, 1)
    random_date = generate_random_date(start_date, end_date)
    assert isinstance(random_date, date)


def test_generate_random_date_range():
    start_date = date(2015, 1, 1)
    end_date = date(2020, 1, 1)
    random_date = generate_random_date(start_date, end_date)
    assert random_date >= start_date
    assert random_date <= end_date


def test_generate_random_date_different_years():
    random_date1 = generate_random_date(date(2020, 1, 1), date(2020, 12, 31))
    random_date2 = generate_random_date(date(2025, 1, 1), date(2025, 12, 31))
    assert random_date1.year == 2020
    assert random_date2.year == 2025


@pytest.mark.parametrize("year", [2020, 2022, 2100])
def test_generate_random_date_valid_years(year):
    random_date = generate_random_date(date(year, 1, 1), date(year, 12, 31))
    assert random_date.year == year


#############################################
# calculate_probabilities_over_period tests #
#############################################

def test_calculate_probabilities_over_period_return_type():
    output = calculate_probabilities_over_period(2020, 5, (0.1, 0.5))
    print(output)
    assert isinstance(output, dict)


def test_calculate_probabilities_over_period_start_end_probs():
    output = calculate_probabilities_over_period(2020, 5, (0.1, 0.5))
    assert output[2020] == 0.1
    assert output[2024] == 0.5


def test_calculate_probabilities_over_period_increasing():
    output = calculate_probabilities_over_period(2020, 5, (0.1, 0.9))
    assert output[2020] < output[2021] < output[2022] < output[2023] < output[2024]


def test_calculate_probabilities_over_period_decreasing():
    output = calculate_probabilities_over_period(2020, 5, (0.9, 0.1))
    assert output[2020] > output[2021] > output[2022] > output[2023] > output[2024]


def test_calculate_probabilities_over_period_invalid_inputs():
    with pytest.raises(ValueError):
        calculate_probabilities_over_period(2020, 0, (0.1, 0.5))

    with pytest.raises(ValueError):
        calculate_probabilities_over_period(2020, 5, (1.1, 0.5))

    with pytest.raises(ValueError):
        calculate_probabilities_over_period(2020, 5, (0.5, 1.5))


##################################
# normalize_probabilities tests #
##################################

def test_normalize_probabilities_normal():
    input_probs = {1: 0.3, 2: 0.5, 3: 0.2}
    expected = [0.3, 0.5, 0.2]
    assert normalize_probabilities(input_probs) == expected


def test_normalize_probabilities_empty_dict():
    with pytest.raises(ValueError):
        normalize_probabilities({})


def test_normalize_probabilities_return_type():
    input_probs = {1: 0.5, 2: 0.3, 3: 0.2}
    assert isinstance(normalize_probabilities(input_probs), list)


def test_normalize_probabilities_sums_to_1():
    input_probs = {1: 0.2, 2: 0.5, 3: 0.3}
    normalized = normalize_probabilities(input_probs)
    assert sum(normalized) == 1


#########################################
# calculate_missing_probabilities tests #
#########################################

def test_calculate_missing_probabilities_empty_dict():
    with pytest.raises(ValueError):
        calculate_missing_probabilities({}, 5)


def test_calculate_missing_probabilities_invalid_period():
    with pytest.raises(ValueError):
        calculate_missing_probabilities({1: 0.5}, 0)


def test_calculate_missing_probabilities_return_type():
    survival_dict = {1: 0.5, 3: 0.3}
    output = calculate_missing_probabilities(survival_dict, 5)
    assert isinstance(output, dict)


def test_calculate_missing_probabilities_interpolation():
    survival_dict = {1: 0.85, 3: 0.45, 5: 0.32}
    output = calculate_missing_probabilities(survival_dict, 5)
    assert {1: 0.85, 2: 0.65, 3: 0.45, 4: 0.385, 5: 0.32} == output


def test_calculate_missing_probabilities_extrapolation():
    survival_dict = {1: 0.85, 3: 0.45, 5: 0.32}
    output = calculate_missing_probabilities(survival_dict, 10)
    assert output[1] == 0.85
    assert output[2] == 0.65
    assert output[3] == 0.45
    assert output[4] == 0.385
    assert output[5] == 0.32
    assert output[6] == 0.255
    assert output[7] == 0.19
    assert output[8] == 0.125
    assert output[9] == 0.06
    assert output[10] == -0.0050000000000000044


if __name__ == "__main__":
    pytest.main()
