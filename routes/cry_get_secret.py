from flask import g
from flask_restx import Namespace, Resource
from http import HTTPStatus
import logging

from globals import auth_parser, LOG_LEVEL
from modules import cry_secrets_management
from modules.cry_auth import auth
from modules.cry_auth_helpers import ip_whitelist_required

logging.basicConfig(level=LOG_LEVEL)

ns = Namespace('get_secret', description='Namespace for fetching stored secrets.')


@ns.route('/<string:app_name>/<string:bucket>/<string:secret_name>')
class GetSecret(Resource):
    """
    Resource to fetch the secret for a given bucket and secret name.
    """

    @auth.login_required
    @ns.expect(auth_parser, params={'app_name': 'Name of the Application',
                                    'bucket': 'Name of the bucket',
                                    'secret_name': 'Name of the secret'}, validate=True)
    @ns.doc(security='apikey')
    @ns.response(HTTPStatus.OK, 'Secret successfully retrieved.')
    @ns.response(HTTPStatus.NOT_FOUND, 'Bucket or secret not found.')
    @ns.response(HTTPStatus.UNAUTHORIZED, 'Unauthorized access.')
    @ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Internal server error encountered.')
    @ip_whitelist_required  # Apply the IP whitelist decorator here
    def get(self, bucket, secret_name, app_name):
        """
        GET method to retrieve the secret for the specified bucket and secret name.

        :param bucket: Name of the bucket containing the secret.
        :param secret_name: Name of the secret to retrieve.
        :param app_name: Application Name for the Bucket.
        :return: A JSON response containing the secret or an error message.
        """
        if not hasattr(g, 'bucket_name'):
            logging.error("bucket_name not found in global context. Token might not be set properly.")
            return {'message': 'Unauthorized access.'}, HTTPStatus.UNAUTHORIZED

        if g.bucket_name != bucket:
            return {'message': 'Unauthorized access to this bucket.'}, HTTPStatus.UNAUTHORIZED

        try:
            if not cry_secrets_management.bucket_exists(bucket, app_name):
                logging.warning(f"Bucket '{bucket}' not found when trying to fetch secret.")
                return {'message': f"Bucket '{bucket}' not found."}, HTTPStatus.NOT_FOUND

            if not cry_secrets_management.secret_exists(bucket, secret_name, app_name):
                logging.warning(f"Secret for '{secret_name}' not found in bucket '{bucket}'.")
                return {'message': f"Secret for '{secret_name}' not found in bucket '{bucket}'."}, HTTPStatus.NOT_FOUND

            secret = cry_secrets_management.retrieve_secret(bucket, secret_name, app_name)
            logging.info(f"Successfully fetched secret for '{secret_name}' from bucket '{bucket}'.")
            return {'secret': secret}, HTTPStatus.OK

        except Exception as e:
            logging.error(f"Error encountered while fetching secret: {str(e)}")
            return {'error': 'Internal server error'}, HTTPStatus.INTERNAL_SERVER_ERROR
