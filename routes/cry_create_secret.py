from flask_restx import Namespace, Resource, fields

from globals import auth_parser
from modules import cry_secrets_management
from modules.cry_auth import auth

ns = Namespace('create_secret', description='Create Secret Route Namespace')

# Model for secret data in request payload
secret_model = ns.model('Secret', {
    'bucket': fields.String(required=True, description='Bucket name'),
    'service_name': fields.String(required=True, description='Service name'),
    'secret': fields.String(required=True, description='The secret data')
})


@ns.route('/create_secret')
class CreateSecret(Resource):
    @ns.expect(auth_parser, secret_model, validate=True)
    @ns.doc(security='apikey')
    @ns.doc(
        responses={200: 'Secret created successfully.', 400: 'Invalid data provided.', 409: 'Secret already exists.'})
    def post(self):
        # Parse the Authorization header to extract the token
        args = auth_parser.parse_args()
        auth_header = args['Authorization']
        if not auth_header.startswith('Bearer '):
            return {'message': 'Invalid token format. Use "Bearer <token>".'}, 401

        token = auth_header[7:]  # Remove 'Bearer ' to get the token value

        # Verify the token using the provided authentication logic
        if not auth.verify_token(token):
            return {'message': 'Invalid token or unauthorized.'}, 401

        data = ns.payload
        bucket = data.get('bucket')
        service_name = data.get('service_name')
        secret = data.get('secret')
        try:
            # Check if the bucket exists
            if not cry_secrets_management.bucket_exists(bucket):
                return {'message': f"Bucket '{bucket}' not found."}, 404

            # Check if the service_name already exists in the bucket
            if cry_secrets_management.secret_exists(bucket, service_name):
                return {'message': f"Secret '{service_name}' already exists in bucket '{bucket}'."}, 409

            # Store the secret if the bucket and service_name exist and secret is not already present
            cry_secrets_management.store_secret(bucket, service_name, secret.encode())  # Convert secret to bytes
            return {'message': f"Secret for '{service_name}' created successfully in '{bucket}'."}, 200
        except Exception as e:
            return {'error': str(e)}, 500
