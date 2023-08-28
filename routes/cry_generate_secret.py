import secrets
import string

from flask_restx import Namespace, Resource, fields

from globals import auth_parser
from modules import cry_secrets_management

ns = Namespace('generate_secret', description='Generate Secret Route Namespace')

# Model for generate_secret
generate_secret_model = ns.model('GenerateSecret', {
    'bucket': fields.String(required=True, description='Bucket name'),
    'service_name': fields.String(required=True, description='Service name')
})


@ns.route('/generate_secret')
class GenerateSecret(Resource):
    @ns.expect(auth_parser, generate_secret_model, validate=True)
    @ns.doc(security='apikey')
    @ns.doc(
        responses={200: 'Secret generated and saved successfully.', 400: 'Invalid data provided.', 409: 'Secret '
                                                                                                        'already '
                                                                                                        'exists.'})
    def post(self):
        data = ns.payload
        bucket = data.get('bucket')
        service_name = data.get('service_name')
        try:
            # Check if the bucket exists
            if not cry_secrets_management.bucket_exists(bucket):
                return {'message': f"Bucket '{bucket}' not found."}, 404

            # Check if the service_name already exists in the bucket
            if cry_secrets_management.secret_exists(bucket, service_name):
                return {'message': f"Secret '{service_name}' already exists in bucket '{bucket}'."}, 409

            # Generate a random secret
            random_secret = ''.join(
                secrets.choice(string.ascii_letters + string.digits) for _ in range(16))

            # Save the generated secret (no need to encode it)
            cry_secrets_management.store_secret(bucket, service_name, random_secret)  # Pass secret as string
            return {'message': f"Random secret for '{service_name}' generated and saved in '{bucket}'."}, 200
        except Exception as e:
            return {'error': str(e)}, 500
