import requests
import datetime

import numpy as np

from carbontracker import exceptions
from carbontracker.emissions.intensity.fetcher import IntensityFetcher
from carbontracker.emissions.intensity import intensity
from typing import Optional

API_URL = "https://api.carbonintensity.org.uk"


class CarbonIntensityGB(IntensityFetcher):
    def suitable(self, g_location):
        return g_location.country == "GB"

    def carbon_intensity(self, g_location, time_from=None, time_to=None):
        carbon_intensity = intensity.CarbonIntensity(g_location=g_location)

        if time_to is not None and time_to > datetime.datetime.utcnow():
            carbon_intensity.is_prediction = True

        try:
            postcode = g_location.postal
            ci = self._carbon_intensity_gb_regional(
                postcode, time_from=time_from, time_to=time_to
            )
        except:
            ci = self._carbon_intensity_gb_national(
                time_from=time_from, time_to=time_to
            )

        carbon_intensity.carbon_intensity = ci

        return carbon_intensity

    def _carbon_intensity_gb_regional(
        self,
        postcode,
        time_from: Optional[datetime.datetime] = None,
        time_to: Optional[datetime.datetime] = None,
    ):
        """ "Retrieves forecasted carbon intensity (gCO2eq/kWh) in GB by
        postcode."""
        url = f"{API_URL}/regional"

        if time_from is not None or time_to is not None:
            from_str, to_str = self._time_from_to_str(time_from, time_to)
            url += f"/intensity/{from_str}/{to_str}"

        url += f"/postcode/{postcode}"
        response = requests.get(url)
        if not response.ok:
            raise exceptions.CarbonIntensityFetcherError(response.json())
        data = response.json()["data"]

        # API has a bug s.t. if we query current then we get a list.
        if time_from is None and time_to is None:
            data = data[0]

        carbon_intensities = []
        for ci in data["data"]:
            carbon_intensities.append(ci["intensity"]["forecast"])
        carbon_intensity = np.mean(carbon_intensities)

        return carbon_intensity

    def _carbon_intensity_gb_national(self, time_from=None, time_to=None):
        """Retrieves forecasted national carbon intensity (gCO2eq/kWh) in GB."""
        url = f"{API_URL}/intensity"

        if time_from is not None or time_to is not None:
            from_str, to_str = self._time_from_to_str(time_from, time_to)
            url += f"/{from_str}/{to_str}"

        response = requests.get(url)
        if not response.ok:
            raise exceptions.CarbonIntensityFetcherError(response.json())
        carbon_intensity = response.json()["data"][0]["intensity"]["forecast"]
        return carbon_intensity

    def _time_from_to_str(
        self,
        time_from: Optional[datetime.datetime],
        time_to: Optional[datetime.datetime],
    ) -> tuple[str, str]:
        """Returns the current date in UTC (from) and time_dur seconds ahead
        (to) in ISO8601 format YYYY-MM-DDThh:mmZ."""
        date_format = "%Y-%m-%dT%H:%MZ"
        time_from = time_from if time_from is not None else datetime.datetime.utcnow()
        time_to = time_to if time_to is not None else datetime.datetime.utcnow()
        from_str = time_from.strftime(date_format)
        to_str = time_to.strftime(date_format)
        return from_str, to_str
