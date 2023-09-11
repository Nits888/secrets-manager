import logging
from flask_restx import Namespace, Resource
from globals import LOG_LEVEL
from modules import cry_secrets_management

logging.basicConfig(level=LOG_LEVEL)

ns = Namespace('get_secrets_list', description='Get Secrets List Route Namespace')


@ns.route('/get_secrets_list/<string:bucket>')
class GetSecretList(Resource):
    """
    Resource to fetch the list of secrets for a given bucket.
    """
    @staticmethod
    def get(bucket):
        """
        GET method to retrieve the list of secrets for the specified bucket.

        :param bucket: Name of the bucket for which to retrieve the secrets list.
        :return: A JSON response containing a list of secrets or an error message.
        """
        try:
            secrets_list = cry_secrets_management.get_secrets(bucket)
            logging.info(f"Successfully fetched secrets list for bucket '{bucket}'.")
            return {'secrets': secrets_list}, 200
        except Exception as e:
            logging.error(f"Error encountered while fetching secrets list for bucket '{bucket}': {str(e)}")
            return {'error': str(e)}, 500
