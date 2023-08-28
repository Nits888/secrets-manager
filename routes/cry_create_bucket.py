from flask_restx import Namespace, Resource, fields

from modules import cry_secrets_management

ns = Namespace('create_bucket', description='Create Bucket Route Namespace')

bucket_model_post = ns.model('UpdateSecret', {
    'bucket': fields.String(required=True, description='Bucket name')
})


@ns.route('/create_bucket')
class CreateBucket(Resource):
    @ns.expect(bucket_model_post, validate=True)
    @ns.doc(responses={200: 'Bucket created successfully.', 400: 'Invalid bucket name.'})
    def post(self):
        data = ns.payload
        bucket = data.get('bucket')
        if cry_secrets_management.bucket_exists(bucket):
            return {'message': f"Bucket '{bucket}' already exists"}, 400
        try:
            success, client_id, client_secret = cry_secrets_management.create_bucket(bucket)
            if success:
                return {
                    'message': f"Bucket '{bucket}' created successfully.",
                    'client_id': client_id,
                    'client_secret': client_secret
                }, 200
            else:
                return {
                    'message': f"Bucket '{bucket}' already exists or "
                               f"invalid bucket name or failed to Create bucket."
                }, 400
        except Exception as e:
            return {'error': str(e)}, 500
