"""
cry_update_secret.py
--------------------

Module for updating secrets in the Secrets Management Service.
"""

import logging
from flask import g
from http import HTTPStatus

from flask_restx import Namespace, Resource, fields

from globals import auth_parser, LOG_LEVEL
from modules import cry_secrets_management
from modules.cry_auth import auth
from modules.cry_auth_helpers import ip_whitelist_required

# Initialize logging with the specified log level from globals
logging.basicConfig(level=LOG_LEVEL)

ns = Namespace('update_secret', description='Route Namespace for Updating Secrets')

# Model for update_secret request payload
update_secret_model = ns.model('UpdateSecret', {
    'app_name': fields.String(required=True, description='Application Name'),
    'bucket': fields.String(required=True, description='Name of the bucket where the secret will be updated'),
    'secret_name': fields.String(required=True, description='Name of the secret to be updated'),
    'secret': fields.String(required=True, description='New secret value')
})


@ns.route('/update_secret')
class UpdateSecret(Resource):
    """
    Resource class for updating secrets.
    Provides an endpoint for updating the value of a given secret in a specified bucket.
    """

    @auth.login_required
    @ns.expect(auth_parser, update_secret_model, validate=True)
    @ns.doc(security='apikey')
    @ns.doc(responses={
        HTTPStatus.OK: 'Secret updated successfully.',
        HTTPStatus.BAD_REQUEST: 'Invalid data provided.',
        HTTPStatus.NOT_FOUND: 'Bucket or secret not found.',
        HTTPStatus.INTERNAL_SERVER_ERROR: 'Internal server error encountered.',
    })
    @ip_whitelist_required  # Apply the IP whitelist decorator here
    def post(self):
        """
        Post endpoint.
        Updates the value of a secret in the specified bucket.
        Returns appropriate response based on the result of the operation.
        """

        data = ns.payload
        bucket = data.get('bucket')
        secret_name = data.get('secret_name')
        new_secret = data.get('secret')
        app_name = data.get('app_name')

        # Check if bucket_name attribute exists in the g object
        if not hasattr(g, 'bucket_name'):
            logging.error("bucket_name not found in global context. Token might not be set properly.")
            return {'message': 'Unauthorized access.'}, HTTPStatus.UNAUTHORIZED

        # Check if the authenticated user's token bucket matches the bucket in the request
        if g.bucket_name != bucket:
            return {'message': 'Unauthorized access to this bucket.'}, HTTPStatus.UNAUTHORIZED

        try:
            # Check if the bucket and secret exist
            if not cry_secrets_management.bucket_exists(bucket, app_name) or \
               not cry_secrets_management.secret_exists(bucket, secret_name, app_name):
                logging.warning(f"Bucket '{bucket}' or secret '{secret_name}' not found when trying to update.")
                return {'message': f"Bucket '{bucket}' or secret '{secret_name}' not found."}, HTTPStatus.NOT_FOUND

            # Update the secret
            cry_secrets_management.update_secret(bucket, secret_name, new_secret, app_name)
            logging.info(f"Secret '{secret_name}' updated successfully in '{bucket}'.")
            return {'message': f"Secret '{secret_name}' updated successfully in '{bucket}'."}, HTTPStatus.OK
        except Exception as e:
            logging.error(f"Error updating secret: {str(e)}")
            return {'message': 'Failed to update secret. Please try again later.'}, HTTPStatus.INTERNAL_SERVER_ERROR
