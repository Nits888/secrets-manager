import logging
from flask import g
from globals import LOG_LEVEL

from flask_restx import Namespace, Resource, fields
from http import HTTPStatus

from globals import auth_parser
from modules import cry_secrets_management
from modules.cry_auth import auth
from modules.cry_auth_helpers import ip_whitelist_required

# Initialize logging with the specified log level from globals
logging.basicConfig(level=LOG_LEVEL)

ns = Namespace('delete_secret', description='Route Namespace for Deleting Secrets')

# Model for secret data deletion in request payload
delete_model = ns.model('DeleteSecret', {
    'app_name': fields.String(required=True, description='Application Name'),
    'bucket': fields.String(required=True, description='Name of the bucket where the secret is stored'),
    'secret_name': fields.String(required=True, description='Name of the secret to be deleted')
})


@ns.route('/<string:app_name>/<string:bucket>/<string:secret_name>')
class DeleteSecret(Resource):
    """
    Resource class for deleting secrets.
    Provides an endpoint for deleting secrets based on a given bucket and secret name.
    """

    @auth.login_required
    @ns.doc(security='apikey')
    @ns.expect(auth_parser, validate=True)
    @ns.doc(responses={
        HTTPStatus.OK: 'Secret deleted successfully.',
        HTTPStatus.BAD_REQUEST: 'Invalid data provided.',
        HTTPStatus.NOT_FOUND: 'Bucket or Secret not found.',
        HTTPStatus.INTERNAL_SERVER_ERROR: 'Internal server error encountered.',
    })
    @ip_whitelist_required  # Apply the IP whitelist decorator here
    def delete(self, bucket, secret_name, app_name):
        """
        Delete endpoint.
        Deletes a secret identified by its bucket and name.
        Returns appropriate response based on the result of the operation.
        """

        # Check if bucket_name attribute exists in the g object
        if not hasattr(g, 'bucket_name'):
            logging.error("bucket_name not found in global context. Token might not be set properly.")
            return {'message': 'Unauthorized access.'}, HTTPStatus.UNAUTHORIZED

        # Check if the authenticated user's token bucket matches the bucket in the request
        if g.bucket_name != bucket:
            return {'message': 'Unauthorized access to this bucket.'}, HTTPStatus.UNAUTHORIZED

        try:
            if (cry_secrets_management.bucket_exists(bucket, app_name)
                    and cry_secrets_management.secret_exists(bucket, secret_name, app_name)):
                cry_secrets_management.delete_secret(bucket, secret_name, app_name)
                logging.info(f"Secret '{secret_name}' deleted successfully from '{bucket}'.")
                return {'message': f"Secret '{secret_name}' deleted successfully from '{bucket}'."}, HTTPStatus.OK
            else:
                logging.warning(f"Bucket '{bucket}' or secret '{secret_name}' not found.")
                return {'message': f"Bucket '{bucket}' or secret '{secret_name}' not found."}, HTTPStatus.NOT_FOUND
        except Exception as e:
            # Log the exception for debugging purposes
            logging.error(f"Error deleting secret: {e}")
            return {'error': 'An error occurred while processing your request.'}, HTTPStatus.INTERNAL_SERVER_ERROR
