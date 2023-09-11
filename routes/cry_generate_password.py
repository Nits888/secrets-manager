import logging
from flask_restx import Namespace, Resource, fields
from modules import cry_utils
from globals import LOG_LEVEL

# Initialize logging with the specified log level
logging.basicConfig(level=LOG_LEVEL)

ns = Namespace('generate_password', description='Route Namespace for Password Generation')

# Model for password length request payload
password_model = ns.model('PasswordRequest', {
    'length': fields.Integer(required=True, description='Desired password length between 8 and 128', min=8, max=128)
})

# Response model describing the possible return values
response_model = ns.model('PasswordResponse', {
    'password': fields.String(description='Generated password'),
    'error': fields.String(description='Error message, if any')
})


@ns.route('/generate_password')
class GeneratePassword(Resource):
    """
    Resource class for generating passwords.
    Provides an endpoint to generate a random password of the specified length.
    """

    @ns.expect(password_model, validate=True)
    @ns.response(200, 'Password generated successfully.', response_model)
    @ns.response(400, 'Bad Request. Password length should be between 8 and 128 characters.', response_model)
    @ns.response(500, 'Internal Server Error.', response_model)
    def post(self):
        """
        Post endpoint.
        Generates a password of the given length and returns it.
        """

        # Retrieve password length from payload
        data = ns.payload
        password_length = data.get('length')

        # Validate the password length
        if not (8 <= password_length <= 128):
            logging.warning("Invalid password length specified.")
            return {'error': 'Password length should be between 8 and 128 characters.'}, 400

        try:
            password = cry_utils.generate_password(password_length)
            logging.info(f"Password of length {password_length} generated successfully.")
            return {'password': password}, 200
        except Exception as e:
            logging.error(f"Error generating password: {str(e)}")
            return {'error': 'Failed to generate password. Please try again later.'}, 500
