"""
@author: S. Alex Yun

This is a testing script to ensure that the REST API is working as intended.
"""
import random
import time
import unittest

import pandas as pd

from flask_testing import TestCase
from main_api import app


class MyTest(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app

    def test_logic_true(self):
        """
        Test for correctness of detect_glare() using 4 major time zones in North America.
        I have generated these data myself to validate true cases.
        """
        true_data = [
            # Canada/Vancouver (Pacific)
            {"lat": 49.2699648,
            "lon": -123.1290368,
            "epoch": 1591351810.154,
            "orientation": 85.1 
            },
            # US/Denver (Mountain)
            {"lat": 39.7392,
            "lon": -104.9903,
            "epoch": 1580568253.467,
            "orientation": -162.7
            },
            # Canada/Winnipeg (Central)
            {"lat": 49.8951,
            "lon": -97.1384,
            "epoch": 1590499473.635,
            "orientation": -138.2
            },
            # US/New York (Eastern)
            {"lat": 40.7128, 
            "lon": -74.0060,
            "epoch": 1601296776.394,
            "orientation": 148.4
            }
        ]
        for location in true_data:
            response = self.client.post("/detect_glare", data=location)
            self.assertEqual(response.json, {"glare": True})

    def test_logic_false(self):
        """
        Test for correctness of detect_glare() using 4 major time zones in North America.
        I have generated these data myself (excluding Vancouver) to validate false cases.
        """
        false_data = [
            # Canada/Vancouver (Pacific)
            {"lat": 49.2699648,
            "lon": -123.1290368,
            "epoch": 1588704959.321,
            "orientation": -10.2
            },
            # US/Denver (Mountain)
            {"lat": 39.7392,
            "lon": -104.9903,
            "epoch": 1577866976.263,
            "orientation": 2.5
            },
            # Canada/Winnipeg (Central)
            {"lat": 49.8951,
            "lon": -97.1384,
            "epoch": 1587898995.932,
            "orientation": 25.6
            },
            # US/New York(Eastern)
            {"lat": 40.7128,
            "lon": -74.0060,
            "epoch": 1598630710.722,
            "orientation": -177.1
            }
        ]
        for location in false_data:
            response = self.client.post("/detect_glare", data=location)
            self.assertEqual(response.json, {"glare": False})

    def test_valid_inputs(self):
        """
        Test using valid inputs (i.e., all the metadata inputs are within the valid range)
        
        dataset from: https://developers.google.com/public-data/docs/canonical/countries_csv
        drop empty values and values that are not within the valid range.
        i.e., countries in the southern hemisphere are dropped.
        """
        country_coordinates = pd.read_csv("country_coordinates.csv")
        country_coordinates.dropna(inplace=True)
        country_coordinates = country_coordinates.query(
            'latitude >= 0 and latitude <= 90 and longitude >= -180 and longitude <=180')
        
        for idx, row in country_coordinates.iterrows():
            response = self.client.post("/detect_glare", data=
                {'lat': row['latitude'],
                'lon': row['longitude'],
                'epoch': random.uniform(0, time.time()),
                'orientation': random.uniform(-180, 180)
            })
            self.assertEqual(response.status_code, 201)
        
    def test_invalid_input_types(self):
        """
        Test to see if the API could handle invalid input data types.
        Given that RequestParser was defined to only accept float,
        it should raise an error with non-float type(s).
        """
        invalid_type_data = [
            {"lat": 49.2699648,
            "lon": "negative 123", # string, should not work
            "epoch": 1588704959.321,
            "orientation": "-10.2"
            },
            {"lat": 49.2699648,
            "lon": -123.1290368,
            "epoch": False, # boolean should not work
            "orientation": -10.2
            },
            {"lat": 49.2699648,
            "lon": -123.1290368,
            "epoch": 1588704959.321,
            "orientation": None # null value should not work
            }
        ]
        for invalid_dt in invalid_type_data:
            response = self.client.post("/detect_glare", data=invalid_dt)
            self.assertEqual(response.status_code, 400)

    def test_invalid_valid_input_types(self):
        """
        These are technically "invalid" data types,
        but the RequestParser should parse them correctly.
        """
        invalid_valid_type_data = [
            {"lat": 49.2699648, 
            "lon": -123.1290368,
            "epoch": "1588704959.321",
            "orientation": "-10.2"
            },
            {"lat": [49.2699648],
            "lon": [-123.1290368],
            "epoch": 1588704959.321,
            "orientation": "-10.2"
            }
        ]
        for valid_valid_dt in invalid_valid_type_data:
            response = self.client.post("/detect_glare", data=valid_valid_dt)
            self.assertEqual(response.status_code, 201)

    def test_invalid_input_range(self):
        """
        Test to see if the API could handle invalid input ranges.
        Given the pre-defined Schema, invalid input range(s) should raise an error.
        """
        invalid_range_data = [
            {"lat": -1.1096235, # invalid type
            "lon": -123.1290368,
            "epoch": 1588704959.321,
            "orientation": -10.2
            },
            {"lat": -1.1096235, # invalid type
            "lon": 480.206395, # invalid type
            "epoch": 1588704959.321,
            "orientation": -10.2
            },
            {"lat": -1.1096235, # invalid type
            "lon": 480.206395, # invalid type
            "epoch": 1588704959.321,
            "orientation": -190.5 # invalid type
            }
        ]
        for invalid_range in invalid_range_data:
            response = self.client.post("/detect_glare", data=invalid_range)
            self.assertEqual(response.status_code, 400)

    def test_missing_arguments(self):
        """
        Test to see if the API could handle missing arguments in the metadata.
        Given that a value was required to be passed with an argument by the RequestParser,
        a missing argument(s) should raise an error.
        """
        missing_arg_data = [
            {"lat": 49.2699648,
            # missing "lon"
            "epoch": 1588704959.321,
            "orientation": -10.2
            },
            {"lat": 49.2699648,
            "lon": -123.1290368
            # missing "lon" and "orientaion"
            }
        ]
        for missing_arg in missing_arg_data:
            response = self.client.post("/detect_glare", data=missing_arg)
            self.assertEqual(response.status_code, 400)

    def test_extra_arguments(self):
        """
        Test to see if the API could handle extra arguments in the metadata.
        It should recognize the extra argument(s) as unknown and raise an error.
        """
        extra_arg_data = [
            {"lat": 49.2699648,
            "lon": -123.1290368,
            "epoch": 1588704959.321,
            "orientation": -10.2,
            "hello": "world" # extra argument
            },
            {"lat": 49.2699648,
            "lon": -123.1290368,
            "location": [49.2699648, -123.1290368], # extra argument
            "epoch": 1588704959.321,
            "orientation": -10.2,
            "refraction": False # extra argument
            }
        ]
        for extra_arg in extra_arg_data:
            response = self.client.post("/detect_glare", data=extra_arg)
            self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()