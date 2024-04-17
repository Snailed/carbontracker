from abc import ABCMeta, abstractmethod
from geocoder.location import Location
from datetime import datetime
from typing import Optional

""" 
    Information about the geocoder object g_location available
    here: https://geocoder.readthedocs.io
"""


class IntensityFetcher:
    __metaclass__ = ABCMeta

    @abstractmethod
    def suitable(self, g_location) -> bool:
        """Returns True if it can be used based on geocoder location."""
        raise NotImplementedError

    @abstractmethod
    def carbon_intensity(
        self,
        g_location,
        time_from: Optional[datetime] = None,
        time_to: Optional[datetime] = None,
    ):
        """
        Returns the carbon intensity by location and time interval.

        Parameters:
        - g_location (Geocoder object): Geocoder location to fetch carbon intensity data for.
        - time_from (datetime, optional): Start time of the interval. Defaults to current time.
        - time_to (datetime, optional): End time of the interval. Defautls to current time.

        Returns:
        - CarbonIntensity: Carbon intensity.

        Raises:
        - NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError
