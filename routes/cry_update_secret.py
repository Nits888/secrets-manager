from flask_restx import Namespace, Resource, fields

from globals import auth_parser
from modules import cry_secrets_management

ns = Namespace('update_secret', description='Update Secret Route Namespace')

# Update the model for update_secret
update_secret_model = ns.model('UpdateSecret', {
    'bucket': fields.String(required=True, description='Bucket name'),
    'service_name': fields.String(required=True, description='Service name'),
    'secret': fields.String(required=True, description='New secret to be updated'),
})


@ns.route('/update_secret')
class UpdateSecret(Resource):
    @ns.expect(auth_parser, update_secret_model, validate=True)
    @ns.doc(security='apikey')
    @ns.doc(responses={200: 'Secret updated successfully.',
                                     400: 'Invalid data provided.', 404: 'Service not found.'})
    def post(self):
        data = ns.payload
        bucket = data.get('bucket')
        service_name = data.get('service_name')
        new_secret = data.get('secret')

        # Check if the bucket exists
        if not cry_secrets_management.bucket_exists(bucket):
            return {'message': f"Bucket '{bucket}' not found."}, 404

        try:
            # Update the secret if it exists
            cry_secrets_management.update_secret(bucket, service_name, new_secret)
            return {'message': f"Secret for '{service_name}' updated successfully in '{bucket}'."}, 200
        except ValueError as e:
            return {'message': str(e)}, 404
