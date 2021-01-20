# @author: S. Alex Yun
# This is a REST API that processes image metadata to determine the presence of direct glare.

from datetime import datetime

from flask import Flask
from flask_restful import Api, Resource, abort, reqparse
from marshmallow import Schema, fields
from marshmallow.validate import Range
from pysolar import solar
from pytz import timezone
from pytz.exceptions import UnknownTimeZoneError
from timezonefinder import TimezoneFinder


app = Flask(__name__)
api = Api(app)


# Request parser, ensuring that the user is:
# (1) inputting all arguments; AND
# (2) passing a valid value (i.e., non-null and float) with the argument
metadata_parser = reqparse.RequestParser()
metadata_parser.add_argument("lat", type=float, required=True,
    help="Latitude of the car must be a floating point number between 0 and 90.")
metadata_parser.add_argument("lon", type=float, required=True,
    help="Longitude of the car must be a floating point number between -180 and 180.")
metadata_parser.add_argument("epoch", type=float, required=True,
    help="Linux epoch or the timestamp must be a floating point number.")
metadata_parser.add_argument("orientation", type=float, required=True,
    help="Orientation of the car travel must be a floating point number between -180 and 180.")


class GlareProcessorSchema(Schema):
    """For object serialization and input data validation (i.e., correct value range)."""
    lat = fields.Float(required=True, validate=Range(min=0, max=90))
    lon = fields.Float(required=True, validate=Range(min=-180, max=180))
    epoch = fields.Float(required=True)
    orientation = fields.Float(required=True, validate=Range(min=-180, max=180))


glare_processor_schema = GlareProcessorSchema()


class GlareProcessor(Resource):
    """POST new image metadata and determine the presence of a direct glare based solely on the metadata."""
    def post(self):
        # throw an error if the request includes an argument(s) that hasn't been defined in the metadata_parser
        parsed_metadata = metadata_parser.parse_args(strict=True)

        errors = glare_processor_schema.validate(parsed_metadata)
        if errors:
            abort(400, message=str(errors))

        return detect_glare(parsed_metadata), 201


def detect_glare(metadata):
    """
    Detect direct glare present if:
    (1) Azimuthal difference between sun and the direction of the car travel is less than 30 degrees; AND
    (2) Altitude of the sun is less than 45 degrees.
    
    Args:
        metadata (dict of str:float): image metadata.
    Returns:
        (dictof str:bool) presence of direct glare.
    """
    tf = TimezoneFinder()
    try:
        tz_name = tf.timezone_at(lng=metadata['lon'], lat=metadata['lat'])
        if tz_name is None:
            tz_name = tf.closest_timezone_at(lng=metadata['lon'], lat=metadata['lat'])
    except UnknownTimeZoneError:
        abort(404, message="We cannot locate your timezone.")
    
    tz = timezone(tz_name)
    aware_dt = datetime.fromtimestamp(metadata['epoch'], tz=tz)
    azimuth, altitude = solar.get_position(metadata['lat'], metadata['lon'], aware_dt)

    # Convert orientation/direction's range from -180-180 to 0-360.
    if metadata['orientation'] < 0:
        car_direction = metadata['orientation'] + 360
    else:
        car_direction = metadata['orientation']
    
    if azimuth - car_direction < 30 and altitude < 45:
        return {'glare': True}
    return {'glare': False}


# Setup the API resource routing
api.add_resource(GlareProcessor, "/detect_glare")


if __name__ == "__main__":
    import logging

    logging.basicConfig(filename='error.log', level=logging.DEBUG) # a simple logger for tracking
    app.run(debug=True) # make sure to turn off debug mode in production