import logging
from http import HTTPStatus

from flask import g
from flask_restx import Namespace, Resource
from globals import LOG_LEVEL, auth_parser
from modules import cry_secrets_management
from modules.cry_auth import auth

logging.basicConfig(level=LOG_LEVEL)

ns = Namespace('get_secrets_list', description='Get Secrets List Route Namespace')


@ns.route('/get_secrets_list/<string:app_name>/<string:bucket>')
class GetSecretList(Resource):
    """
    Resource to fetch the list of secrets for a given bucket.
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
    def get(self, bucket, app_name):
        """
        GET method to retrieve the list of secrets for the specified bucket.

        :param bucket: Name of the bucket for which to retrieve the secrets list.
        :param app_name: Application Name
        :return: A JSON response containing a list of secrets or an error message.
        """
        if not hasattr(g, 'bucket_name'):
            logging.error("bucket_name not found in global context. Token might not be set properly.")
            return {'message': 'Unauthorized access.'}, HTTPStatus.UNAUTHORIZED

        if g.bucket_name != bucket:
            return {'message': 'Unauthorized access to this bucket.'}, HTTPStatus.UNAUTHORIZED

        try:
            secrets_list = cry_secrets_management.get_secrets(bucket, app_name)
            logging.info(f"Successfully fetched secrets list for bucket '{bucket}'.")
            return {'secrets': secrets_list}, 200
        except Exception as e:
            logging.error(f"Error encountered while fetching secrets list for bucket '{bucket}': {str(e)}")
            return {'error': str(e)}, 500
