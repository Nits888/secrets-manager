from flask_restx import Namespace, Resource, fields

from globals import auth_parser
from modules import cry_secrets_management

ns = Namespace('delete_secret', description='Delete Secret Route Namespace')

# Model for secret data deletion in request payload
delete_model = ns.model('DeleteSecret', {
    'bucket': fields.String(required=True, description='Bucket name'),
    'service_name': fields.String(required=True, description='Service name')
})


@ns.route('/delete_secret')
class DeleteSecret(Resource):
    @ns.doc(security='apikey')
    @ns.expect(auth_parser, delete_model, validate=True)
    @ns.doc(responses={200: 'Secret deleted successfully.', 400: 'Invalid data provided.'})
    def delete(self):
        data = ns.payload
        bucket = data.get('bucket')
        service_name = data.get('service_name')
        try:
            if (cry_secrets_management.bucket_exists(bucket)
                    and cry_secrets_management.secret_exists(bucket, service_name)):
                cry_secrets_management.delete_secret(bucket, service_name)
                return {'message': f"Secret '{service_name}' deleted successfully from '{bucket}'."}, 200
            else:
                return {'message': f"Bucket '{bucket}' or secret '{service_name}' not found."}, 404
        except Exception as e:
            return {'error': str(e)}, 500
