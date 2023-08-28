from flask_restx import Namespace, Resource

from modules import cry_secrets_management

ns = Namespace('get_secrets_list', description='Get Secrets List Route Namespace')


@ns.route('/get_secrets_list/<string:bucket>')
class GetSecretList(Resource):
    @staticmethod
    def get(bucket):
        try:
            secrets_list = cry_secrets_management.get_secrets(bucket)
            return {'secrets': secrets_list}, 200
        except Exception as e:
            return {'error': str(e)}, 500
