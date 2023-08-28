from flask_restx import Namespace, Resource

from globals import auth_parser
from modules import cry_secrets_management

ns = Namespace('get_secret', description='Get Secret Route Namespace')


@ns.route('/get_secret/<string:bucket>/<string:service_name>')
class GetSecret(Resource):
    @ns.doc(security='apikey')
    @ns.doc(auth_parser, params={'bucket': 'Bucket name', 'service_name': 'Service name'})
    @ns.doc(responses={200: 'Secret retrieved successfully.', 404: 'Bucket or secret not found.'})
    def get(self, bucket, service_name):
        try:
            if (cry_secrets_management.bucket_exists(bucket) and
                    cry_secrets_management.secret_exists(bucket, service_name)):
                secret = cry_secrets_management.retrieve_secret(bucket, service_name)
                return {'secret': secret}, 200
            else:
                return {'message': f"Bucket '{bucket}' or secret '{service_name}' not found."}, 404
        except Exception as e:
            return {'error': str(e)}, 500
