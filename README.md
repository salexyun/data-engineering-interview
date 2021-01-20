# data-engineering-interview
This repo contains scripts that were written for a data engineering interview.

## Dependencies
- Python 3.7
- Please see requirements.txt for additional packages.

## Instructions
- Big picture: to develop a vision system (camera + object detection).
- Classification problem: to detect the presence (0/1) of direct glare.
- Hardware: forward-facing camera.
- Data: images of driving (with metadata):
    * lat (float; 0-90 => northern hemisphere): latitude in which the image was taken.
    * lon (float; -180-180): longitude in which the image was taken.
    * epoch (float): Linux epoch in second (timezone independent).
    * orientation (float; -180-180): eastward orientation of car travel from true north.
- Definition of direct glare:
    1. Azimuthal difference between the sun and the direction of the car travel < 30 degrees; AND
    2. Altitude of the sun < 45 degrees.

## Thought Process and Design Choices
- I chose to use Flask over Django; as a microframework, it is simple enough to create an effective REST API, but can easily be extended to support additional functionality in the future.
- Given that there was no instruction regarding the database, I simply did not implement one. Otherwise I would normally use Flask-SQLAlchemy and have additional methods (e.g., POST, GET, DELETE) to support CRUD operations.
- I used Flask-RESTful, an extension of Flask, which is designed to provide lightweight abstraction specifically for building REST APIs.
- Aside from handling the POST request, the main focus was on writing the function that detects the glare:
    * This requires the calculation of the azimuth and altitude of the sun.
        - These require variables, including position of the observer (i.e., car) and the sun, time, local hour angle, solar declination, and etc.
    * These calculations are done by the library Pysolar, which calculates the azimuth and altitude of the sun based on observer's location (latitude and longitude) and time (Linux epoch). Note that the time input must be given as a timezone-aware datetime object. This means that the Linux epoch has to be converted from float to datetime and add the timezone information; hence, the use of timezonefinder and pytz packages.
    * This, however, poses a few challenges, specifically regarding the identification of the timezone. It is entirely possible that we cannot locate the timezone of the image taken correctly. This calls for a try-except block where we try to get the exact timezone, if this fails, we try to get the closest time zone, and if this fails, we raise an error.
    * When calculating the azimuthal difference, note the azimuth and the orientation occupy different ranges. The range of the orientation can be changed from -180-180 to 0-360 by adding 360 to negative degrees, so it occupies the same range as the azimuth.

## Limitations
- At its current formulation, latitude between -90-0 is ignored, meaning we do not capture locations in the southern hemisphere. If we extend the API to support this, we'll have to note that the azimuth is referend to due south in the northern hemisphere and to due north in the southern hemisphere (https://www.sciencedirect.com/topics/engineering/surface-azimuth-angle).
- Approximating azimuth is tricky given that one must consider refraction based on temperature and pressure of the location in which the image was taken.
    * Technically, it would be best to have a hardware that captures these variables when taking the images.
    * Because we already have an established dataset, a possible solution is to call an existing API to obtain these variables to ensure the highest accuracy of our azimuth calculation.
- Pysolar currently raises the following error:
    * UserWarning: I don't know about leap seconds after 2018 (leap_seconds_base_year + len(leap_seconds_adjustments) - 1)
    * I do not believe this is a critical issue for our current system.

## Note
- The API's security was not tested
    1. POST is a relatively safe request.
    2. There is no database -> cannot try SQL injections.
    3. DDos is possible, but cannot do anything from the code side.
- The load testing tool may seem excessive; however, it is handy to have it ready in case we plan to scale up the API that must handle 100s and 1000s of requests.
