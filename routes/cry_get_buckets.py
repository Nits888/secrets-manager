"""
cry_get_buckets.py
------------------

Module for retrieving the list of available buckets.
"""

import logging
from flask_restx import Namespace, Resource
from modules import cry_secrets_management
from globals import LOG_LEVEL

# Initialize logging with the specified log level
logging.basicConfig(level=LOG_LEVEL)

ns = Namespace('get_buckets', description='Route Namespace to retrieve available buckets.')


@ns.route('/buckets')
class Buckets(Resource):
    """
    Resource class for retrieving available buckets.
    Provides an endpoint to list all buckets.
    """

    @ns.response(200, 'Buckets retrieved successfully.')
    @ns.response(500, 'Internal Server Error.')
    def get(self):
        """
        Get endpoint.
        Returns a list of all available buckets.
        """

        try:
            # Retrieve the list of buckets
            buckets = cry_secrets_management.get_buckets()
            logging.info(f"Retrieved {len(buckets)} buckets successfully.")
            return {'buckets': buckets}, 200
        except Exception as e:
            # Log the error and return a 500 status code
            logging.error(f"Error retrieving buckets: {str(e)}")
            return {'error': 'Failed to retrieve buckets. Please try again later.'}, 500
