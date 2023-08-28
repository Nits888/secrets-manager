from flask_restx import Namespace, Resource, fields

from modules import cry_utils

ns = Namespace('generate_password', description='Create Bucket Route Namespace')

# Model for password data in request payload
password_model = ns.model('Password', {
    'length': fields.Integer(required=True, description='Password length')
})


@ns.route('/generate_password')
class GeneratePassword(Resource):
    @ns.expect(password_model, validate=True)
    @ns.doc(responses={200: 'Password generated successfully.'})
    def post(self):
        data = ns.payload
        password_length = data.get('length')
        try:
            password = cry_utils.generate_password(password_length)
            return {'password': password}, 200
        except Exception as e:
            return {'error': str(e)}, 500
