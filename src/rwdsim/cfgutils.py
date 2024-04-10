from io import TextIOWrapper

from .classes import SimParams


def read_config(config_file: TextIOWrapper) -> SimParams:
    """Reads simulation parameters from a configuration file and populates the SimParams named tuple.

    Args:
        config_file_path (str): Path to the configuration file.

    Returns:
        SimParams: A named tuple containing all simulation parameters.
    """
    params: SimParams = SimParams.model_validate_json(''.join(config_file.readlines()))
    return params
