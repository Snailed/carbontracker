from unittest import TestCase, mock
import datetime
from carbontracker.emissions.intensity.fetchers import carbonintensitygb
from carbontracker import exceptions


class TestCarbonIntensityGB(TestCase):
    def setUp(self):
        self.fetcher = carbonintensitygb.CarbonIntensityGB()

    def test_suitable_with_gb_location(self):
        g_location = mock.MagicMock(country="GB")
        result = self.fetcher.suitable(g_location)
        self.assertTrue(result)

    def test_suitable_with_non_gb_location(self):
        g_location = mock.MagicMock(country="US")
        result = self.fetcher.suitable(g_location)
        self.assertFalse(result)

    @mock.patch("carbontracker.emissions.intensity.fetchers.carbonintensitygb.datetime")
    @mock.patch(
        "carbontracker.emissions.intensity.fetchers.carbonintensitygb.requests.get"
    )
    def test_carbon_intensity_gb_regional_prediction(self, mock_get, mock_datetime):
        mock_response = mock.MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": {
                "data": [
                    {
                        "from": "2023-05-20T00:00Z",
                        "to": "2023-05-20T01:00Z",
                        "intensity": {"forecast": 200},
                    },
                    {
                        "from": "2023-05-20T01:00Z",
                        "to": "2023-05-20T02:00Z",
                        "intensity": {"forecast": 300},
                    },
                ]
            }
        }
        mock_get.return_value = mock_response
        g_location = mock.MagicMock(postal="AB12 3CD")
        time_dur = 3600

        # Patch datetime.now to return a fixed value
        mock_datetime.datetime.now.return_value = datetime.datetime(2023, 5, 20, 0, 0)

        # Patch datetime.timedelta to return a fixed value
        mock_datetime.timedelta().__radd__().strftime.return_value = "2023-05-20T01:00Z"

        result = self.fetcher._carbon_intensity_gb_regional(
            g_location.postal,
            time_from=None,
            time_to=datetime.datetime(2023, 5, 20, 0, 0)
            + datetime.timedelta(seconds=time_dur),
        )

        from_str = "2023-05-20T00:00Z"
        to_str = "2023-05-20T01:00Z"

        mock_get.assert_called_once_with(
            f"https://api.carbonintensity.org.uk/regional/intensity/{from_str}/{to_str}/postcode/AB12 3CD"
        )
        self.assertEqual(result, 250)

    @mock.patch(
        "carbontracker.emissions.intensity.fetchers.carbonintensitygb.requests.get"
    )
    def test_carbon_intensity_gb_regional_with_error_response(self, mock_get):
        mock_response = mock.MagicMock()
        mock_response.ok = False
        mock_response.json.return_value = {"error": "Invalid postcode"}
        mock_get.return_value = mock_response
        g_location = mock.MagicMock(postal="AB12 3CD")
        time_dur = 3600

        with self.assertRaises(exceptions.CarbonIntensityFetcherError):
            self.fetcher._carbon_intensity_gb_regional(
                g_location.postal,
                time_from=None,
                time_to=datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(seconds=time_dur),
            )

    @mock.patch("carbontracker.emissions.intensity.fetchers.carbonintensitygb.datetime")
    @mock.patch(
        "carbontracker.emissions.intensity.fetchers.carbonintensitygb.requests.get"
    )
    def test_carbon_intensity_gb_national(self, mock_get, mock_datetime):
        mock_response = mock.MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": [
                {
                    "intensity": {"forecast": 250},
                }
            ]
        }
        mock_get.return_value = mock_response
        time_dur = 3600

        # Set fixed values for from_str and to_str
        from_str = "2023-05-20T00:00Z"
        to_str = "2023-05-20T01:00Z"

        # Patch datetime.now to return a fixed value
        mock_datetime.datetime.now.return_value = datetime.datetime(2023, 5, 20, 0, 0)

        # Patch datetime.timedelta to return a fixed value
        mock_datetime.timedelta().__radd__().strftime.return_value = to_str

        result = self.fetcher._carbon_intensity_gb_national(
            time_from=None,
            time_to=datetime.datetime(2023, 5, 20, 0, 0)
            + datetime.timedelta(seconds=time_dur),
        )

        mock_get.assert_called_once_with(
            f"https://api.carbonintensity.org.uk/intensity/{from_str}/{to_str}"
        )
        self.assertEqual(result, 250)

    @mock.patch(
        "carbontracker.emissions.intensity.fetchers.carbonintensitygb.requests.get"
    )
    def test_carbon_intensity_gb_national_with_error_response(self, mock_get):
        mock_response = mock.MagicMock()
        mock_response.ok = False
        mock_response.json.return_value = {"error": "Invalid request"}
        mock_get.return_value = mock_response
        time_dur = 3600

        with self.assertRaises(exceptions.CarbonIntensityFetcherError):
            self.fetcher._carbon_intensity_gb_national(
                time_from=None,
                time_to=datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(time_dur),
            )

    @mock.patch(
        "carbontracker.emissions.intensity.fetchers.carbonintensitygb.requests.get"
    )
    def test_carbon_intensity_gb_national_historical(self, mock_get):
        mock_response = mock.MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": [
                {
                    "from": "2023-05-19T23:30Z",
                    "to": "2023-05-20T00:00Z",
                    "intensity": {"forecast": 134, "actual": 127, "index": "moderate"},
                },
                {
                    "from": "2023-05-20T00:00Z",
                    "to": "2023-05-20T00:30Z",
                    "intensity": {"forecast": 133, "actual": 129, "index": "moderate"},
                },
            ]
        }
        mock_get.return_value = mock_response

        carbon_intensity = self.fetcher._carbon_intensity_gb_national(
            time_from=datetime.datetime(2023, 5, 20, 0, 0),
            time_to=datetime.datetime(2023, 5, 21, 0, 0),
        )
        self.assertEqual(carbon_intensity, 133.5)

    @mock.patch(
        "carbontracker.emissions.intensity.fetchers.carbonintensitygb.requests.get"
    )
    def test_carbon_intensity_gb_regional_historical(self, mock_get):
        mock_response = mock.MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": {
                "data": [
                    {
                        "from": "2023-05-19T23:30Z",
                        "to": "2023-05-20T00:00Z",
                        "intensity": {
                            "forecast": 134,
                            "actual": 127,
                            "index": "moderate",
                        },
                    },
                    {
                        "from": "2023-05-20T00:00Z",
                        "to": "2023-05-20T00:30Z",
                        "intensity": {
                            "forecast": 133,
                            "actual": 129,
                            "index": "moderate",
                        },
                    },
                ]
            }
        }
        mock_get.return_value = mock_response

        carbon_intensity = self.fetcher._carbon_intensity_gb_regional(
            "RG10",
            time_from=datetime.datetime(2023, 5, 20, 0, 0),
            time_to=datetime.datetime(2023, 5, 21, 0, 0),
        )
        self.assertEqual(carbon_intensity, 133.5)

    def test_time_from_to_str(self):
        time_dur = 3600
        time_from = datetime.datetime.now(datetime.timezone.utc)
        time_to = time_from + datetime.timedelta(seconds=time_dur)
        from_str = time_from.strftime("%Y-%m-%dT%H:%MZ")
        to_str = time_to.strftime("%Y-%m-%dT%H:%MZ")

        result = self.fetcher._time_from_to_str(time_from, time_to)

        self.assertEqual(result, (from_str, to_str))

    @mock.patch(
        "carbontracker.emissions.intensity.fetchers.carbonintensitygb.requests.get"
    )
    def test_carbon_intensity_with_postal(self, mock_get):
        mock_response = mock.MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": [{"intensity": {"forecast": 250}}]}
        mock_get.return_value = mock_response

        mock_get.__getitem__.return_value = mock_response
        g_location = mock.MagicMock(postal="AB12 3CD", country="GB")
        time_dur = 3600

        carbon_intensity_obj = self.fetcher.carbon_intensity(
            g_location,
            None,
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(time_dur),
        )
        self.assertEqual(carbon_intensity_obj.carbon_intensity, 250)
        self.assertEqual(carbon_intensity_obj.is_prediction, True)

    @mock.patch(
        "carbontracker.emissions.intensity.fetchers.carbonintensitygb.requests.get"
    )
    def test_carbon_intensity_without_postal(self, mock_get):
        mock_response = mock.MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": [{"intensity": {"forecast": 250}}]}
        mock_get.return_value = mock_response

        g_location = mock.MagicMock(country="GB")
        time_dur = 3600

        carbon_intensity_obj = self.fetcher.carbon_intensity(
            g_location,
            None,
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(time_dur),
        )
        self.assertEqual(carbon_intensity_obj.carbon_intensity, 250)
        self.assertEqual(carbon_intensity_obj.is_prediction, True)

    @mock.patch(
        "carbontracker.emissions.intensity.fetchers.carbonintensitygb.requests.get"
    )
    def test_carbon_intensity_gb_regional_without_time_dur(self, mock_get):
        mock_response = mock.MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": [{"intensity": {"forecast": 250}}]}
        mock_get.return_value = mock_response

        g_location = mock.MagicMock(postal="AB12 3CD", country="GB")

        carbon_intensity_obj = self.fetcher.carbon_intensity(g_location, None, None)
        self.assertEqual(carbon_intensity_obj.carbon_intensity, 250)
