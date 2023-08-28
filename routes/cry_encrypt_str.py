from flask_restx import Namespace, Resource, fields

from modules import cry_encryption

ns = Namespace('encrypt_str', description='Encrypt String Route Namespace')

# Encrypt Model
encrypt_model = ns.model('Encrypt', {
    'text': fields.String(required=True, description='Text to encrypt'),
})


@ns.route('/encrypt_string')
class EncryptString(Resource):
    @ns.doc('encrypt_string')
    @ns.expect(encrypt_model, validate=True)
    @ns.response(200, 'String encrypted successfully.')
    def post(self):
        data = ns.payload
        text = data.get('text')
        try:
            encrypted_text = cry_encryption.encrypt_text(text)
            return {'encrypted_text': encrypted_text}, 200
        except Exception as e:
            return {'error': str(e)}, 500
