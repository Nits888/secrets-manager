from http import HTTPStatus
from flask_restx import Namespace, Resource, fields
from globals import auth_parser, LOG_LEVEL
from modules.cry_auth import auth
from modules import cry_encryption
import logging

# Initialize logging with the specified log level
logging.basicConfig(level=LOG_LEVEL)

ns = Namespace('encrypt_str', description='Route Namespace for Encrypting Strings')

# Model for the encryption request payload
encrypt_model = ns.model('Encrypt', {
    'text': fields.String(required=True, description='Text to be encrypted'),
})


@ns.route('/encrypt_string')
class EncryptString(Resource):
    """
    Resource class for encrypting strings.
    Provides an endpoint for encrypting a given text string.
    """

    # @auth.login_required
    @ns.expect(encrypt_model, validate=True)
    # @ns.doc(security='apikey')
    @ns.doc(responses={
        HTTPStatus.OK: 'String encrypted successfully.',
        # HTTPStatus.BAD_REQUEST: 'Invalid data provided.',
        # HTTPStatus.UNAUTHORIZED: 'Invalid token or unauthorized access.',
        HTTPStatus.INTERNAL_SERVER_ERROR: 'Internal server error encountered.',
    })
    def post(self):
        """
        Post endpoint.
        Encrypts the provided text string and returns the encrypted value.
        """

        # Check if the text to be encrypted has been provided
        data = ns.payload
        text = data.get('text')
        if not text:
            logging.warning("No text provided for encryption.")
            return {'message': 'Text to be encrypted is required.'}, HTTPStatus.BAD_REQUEST

        try:
            encrypted_text = cry_encryption.encrypt_text(text)
            logging.info("String encrypted successfully.")
            return {'encrypted_text': encrypted_text}, HTTPStatus.OK
        except Exception as e:
            logging.error(f"Error encrypting text: {str(e)}")
            return {'error': 'Failed to encrypt text. Please try again later.'}, HTTPStatus.INTERNAL_SERVER_ERROR
