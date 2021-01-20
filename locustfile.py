"""
@author: S. Alex Yun

This is a simple load testing tool.

After running the main_api.py, run this script:
$ locust
>>> Starting web interface at <URL> (accepting connections from all network interfaces)

Open up a browser and point it to the stated URL (e.g., http://0.0.0.0:8089).
Fill out the form, making sure the host matches the server from main_api.py
(e.g., http://127.0.0.1:5000)
"""
from locust import HttpUser, task


class QuickstartUser(HttpUser):
    @task
    def detect(self):
        self.client.post("/detect_glare",
            {"lat": 49.2699648,
            "lon": -123.1290368,
            "epoch": 1588704959.321,
            "orientation": -10.2
            }
        )