from flask_restx import Namespace, Resource, fields

from modules import cry_encryption

ns = Namespace('decrypt_str', description='Decrypt String Route Namespace')

# Decrypt Model
decrypt_model = ns.model('Decrypt', {
    'text': fields.String(required=True, description='Text to decrypt'),
    'salt': fields.String(required=True, description='Salt to decrypt'),
})


@ns.route('/decrypt_string')
class DecryptString(Resource):
    @ns.doc('decrypt_string')
    @ns.expect(decrypt_model, validate=True)
    @ns.response(200, 'String decrypted successfully.')
    def post(self):
        data = ns.payload
        text = data.get('text')
        salt = data.get('salt')
        try:
            decrypted_text = cry_encryption.decrypt_text(text, salt)
            return {'decrypted_text': decrypted_text}, 200
        except Exception as e:
            return {'error': str(e)}, 500
