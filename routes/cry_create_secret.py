from flask import g
from flask_restx import Namespace, Resource, fields
from http import HTTPStatus
import logging

from globals import auth_parser, LOG_LEVEL
from modules import cry_secrets_management
from modules.cry_auth import auth

# Initialize logging with the specified log level from globals
logging.basicConfig(level=LOG_LEVEL)

ns = Namespace('create_secret', description='Secrets Management Route Namespace')

# Define the model for the secret data in the request payload
secret_model = ns.model('Secret', {
    'bucket': fields.String(required=True, description='Bucket name'),
    'secret_name': fields.String(required=True, description='Secret name'),
    'secret': fields.String(required=True, description='The secret data')
})


@ns.route('/')
class SecretResource(Resource):
    """
    Resource class for secrets management. Provides an endpoint for creating secrets.
    """

    @auth.login_required
    @ns.expect(auth_parser, secret_model, validate=True)
    @ns.doc(security='apikey')
    @ns.doc(
        responses={
            HTTPStatus.OK: 'Secret created successfully.',
            HTTPStatus.BAD_REQUEST: 'Invalid data provided.',
            HTTPStatus.CONFLICT: 'Secret already exists.',
            HTTPStatus.INTERNAL_SERVER_ERROR: 'Internal server error.'
        })
    def post(self):
        """
        Endpoint to store a new secret. Requires bucket name, secret name, and the secret data.
        Returns a JSON response indicating the result of the operation.
        """
        data = ns.payload
        bucket = data.get('bucket')
        secret_name = data.get('secret_name')

        # Check if bucket_name attribute exists in the g object
        if not hasattr(g, 'bucket_name'):
            logging.error("bucket_name not found in global context. Token might not be set properly.")
            return {'message': 'Unauthorized access.'}, HTTPStatus.UNAUTHORIZED

        # Check if the authenticated user's token bucket matches the bucket in the request
        if g.bucket_name != bucket:
            return {'message': 'Unauthorized access to this bucket.'}, HTTPStatus.UNAUTHORIZED

        secret = data.get('secret')
        logging.info(f"Attempting to create secret: {secret_name} in bucket: {bucket}.")
        return create_secret(bucket, secret_name, secret)


def create_secret(bucket, secret_name, secret):
    """
    Helper function to create a new secret in the system.
    """
    # Check if the specified bucket exists
    if not cry_secrets_management.bucket_exists(bucket):
        logging.warning(f"Bucket '{bucket}' not found when trying to create a secret.")
        return {'message': f"Bucket '{bucket}' not found."}, HTTPStatus.NOT_FOUND

    # Check if a secret with the specified name already exists in the bucket
    if cry_secrets_management.secret_exists(bucket, secret_name):
        logging.warning(f"Secret '{secret_name}' already exists in bucket '{bucket}'.")
        return {'message': f"Secret '{secret_name}' already exists in bucket '{bucket}'."}, HTTPStatus.CONFLICT

    # Store the secret in the specified bucket with the given name
    cry_secrets_management.store_secret(bucket, secret_name, secret.encode())
    logging.info(f"Secret for '{secret_name}' created successfully in '{bucket}'.")
    return {'message': f"Secret for '{secret_name}' created successfully in '{bucket}'."}, HTTPStatus.OK
