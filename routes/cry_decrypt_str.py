from http import HTTPStatus
from flask_restx import Namespace, Resource, fields
from globals import auth_parser, LOG_LEVEL
from modules.cry_auth import auth
from modules import cry_encryption
import logging

# Initialize logging with the specified log level
logging.basicConfig(level=LOG_LEVEL)

ns = Namespace('decrypt_str', description='Route Namespace for Decrypting Strings')

# Model for the decryption request payload
decrypt_model = ns.model('Decrypt', {
    'text': fields.String(required=True, description='Text to decrypt'),
    'salt': fields.String(required=True, description='Salt used for decryption'),
})


@ns.route('/decrypt_string')
class DecryptString(Resource):
    """
    Resource class for decrypting strings.
    Provides an endpoint for decrypting a given text string using the provided salt.
    """

    # @auth.login_required
    @ns.expect(decrypt_model, validate=True)
    # @ns.doc(security='apikey')
    @ns.doc(responses={
        HTTPStatus.OK: 'String decrypted successfully.',
        # HTTPStatus.BAD_REQUEST: 'Invalid data provided.',
        # HTTPStatus.UNAUTHORIZED: 'Invalid token or unauthorized access.',
        HTTPStatus.INTERNAL_SERVER_ERROR: 'Internal server error encountered.',
    })
    def post(self):
        """
        Post endpoint.
        Decrypts the provided text string using the provided salt and returns the decrypted value.
        """

        # Check if the text and salt to be decrypted have been provided
        data = ns.payload
        text = data.get('text')
        salt = data.get('salt')
        if not text or not salt:
            logging.warning("No text or salt provided for decryption.")
            return {'message': 'Text and salt for decryption are required.'}, HTTPStatus.BAD_REQUEST

        try:
            decrypted_text = cry_encryption.decrypt_text(text, salt)
            logging.info("String decrypted successfully.")
            return {'decrypted_text': decrypted_text}, HTTPStatus.OK
        except Exception as e:
            logging.error(f"Error decrypting text: {str(e)}")
            return {'error': 'Failed to decrypt text. Please try again later.'}, HTTPStatus.INTERNAL_SERVER_ERROR
