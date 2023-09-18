import logging
from flask import g
from http import HTTPStatus

from flask_restx import Namespace, Resource, fields

from globals import auth_parser
from modules import cry_secrets_management, cry_utils
from modules.cry_auth import auth

# Initialize logging with the specified log level from globals
logging.basicConfig(level=logging.INFO)

ns = Namespace('generate_secret', description='Route Namespace for Generating and Storing Secrets')

# Model for generate_secret request payload
generate_secret_model = ns.model('GenerateSecret', {
    'app_name': fields.String(required=True, description='Application Name'),
    'bucket': fields.String(required=True, description='Name of the bucket where the secret will be stored'),
    'secret_name': fields.String(required=True, description='Name of the secret to be generated and stored')
})


@ns.route('/generate_secret')
class GenerateSecret(Resource):
    """
    Resource class for generating secrets.
    Provides an endpoint for generating a random secret and storing it based on a given bucket and secret name.
    """

    @auth.login_required
    @ns.expect(auth_parser, generate_secret_model, validate=True)
    @ns.doc(security='apikey')
    @ns.doc(responses={
        HTTPStatus.OK: 'Secret generated and saved successfully.',
        HTTPStatus.BAD_REQUEST: 'Invalid data provided.',
        HTTPStatus.CONFLICT: 'Secret already exists.',
        HTTPStatus.NOT_FOUND: 'Bucket not found.',
        HTTPStatus.INTERNAL_SERVER_ERROR: 'Internal server error encountered.',
    })
    def post(self):
        """
        Post endpoint.
        Generates a random secret and stores it in the specified bucket with the given name.
        Returns appropriate response based on the result of the operation.
        """

        data = ns.payload
        bucket = data.get('bucket')
        secret_name = data.get('secret_name')
        app_name = data.get('app_name')

        # Check if bucket_name attribute exists in the g object
        if not hasattr(g, 'bucket_name'):
            logging.error("bucket_name not found in global context. Token might not be set properly.")
            return {'message': 'Unauthorized access.'}, HTTPStatus.UNAUTHORIZED

        # Check if the authenticated user's token bucket matches the bucket in the request
        if g.bucket_name != bucket:
            return {'message': 'Unauthorized access to this bucket.'}, HTTPStatus.UNAUTHORIZED

        try:
            # Check if the bucket exists
            if not cry_secrets_management.bucket_exists(bucket, app_name):
                logging.warning(f"Bucket '{bucket}' not found when trying to generate a secret.")
                return {'message': f"Bucket '{bucket}' not found."}, HTTPStatus.NOT_FOUND

            # Check if the secret_name already exists in the bucket
            if cry_secrets_management.secret_exists(bucket, secret_name, app_name):
                logging.warning(f"Secret '{secret_name}' already exists in bucket '{bucket}'.")
                return {'message': f"Secret '{secret_name}' already exists in bucket '{bucket}'."}, HTTPStatus.CONFLICT

            # Generate a random secret using the utility function
            random_secret = cry_utils.generate_random_secret()

            # Save the generated secret (no need to encode it)
            cry_secrets_management.store_secret(bucket, secret_name, random_secret, app_name)
            logging.info(f"Random secret for '{secret_name}' generated and saved in '{bucket}'.")
            return {'message': f"Random secret for '{secret_name}' generated and saved in '{bucket}'."}, HTTPStatus.OK
        except Exception as e:
            logging.error(f"Error generating secret: {str(e)}")
            return ({'message': 'Failed to generate and save secret. Please try again later.'},
                    HTTPStatus.INTERNAL_SERVER_ERROR)
