from flask_restx import Namespace, Resource

from modules import cry_secrets_management

ns = Namespace('get_buckets', description='Get Buckets Route Namespace')


@ns.route('/buckets')
class Buckets(Resource):
    @staticmethod
    def get():
        try:
            buckets = cry_secrets_management.get_buckets()
            return {'buckets': buckets}, 200
        except Exception as e:
            return {'error': str(e)}, 500
