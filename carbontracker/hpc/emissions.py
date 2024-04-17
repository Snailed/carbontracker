import numpy as np
import json
from emissions.intensity.fetchers import electricitymaps
import exceptions
from emissions.intensity.intensity import carbon_intensity
import loggerutil


def job_emissions(start, end, consumed_energy_J, api_key=""):
    # Taken from tracker.py
    api_dict = {}
    if isinstance(api_key, str):
        api_dict = json.loads(api_key)
    if isinstance(api_key, dict):
        api_dict = api_key

    logger = loggerutil.Logger(log_dir=None, verbose=1, log_prefix="")

    for name, key in api_dict.items():
        if name.lower() == "electricitymaps":
            electricitymaps.ElectricityMap.set_api_key(key)
        else:
            raise exceptions.FetcherNameError(f"Invalid API name '{name}' given.")

    intensity = carbon_intensity(logger)

    mean_carbon_intensity = np.mean(
        get_carbon_intensity(
            start, end, api_key
        ),  # i.e. for each row in start, end, get carbon intensities as list
        axis=1,
    )  # gCO2eq/kWh

    consumed_energy_kWh = consumed_energy_J * 2.77777778e-7
    return consumed_energy_kWh * mean_carbon_intensity
