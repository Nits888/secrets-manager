import datetime

from flask_restx import Namespace, Resource, fields
from http import HTTPStatus
import logging
from os import environ

from modules.cry_auth import verify_token
from globals import LOG_LEVEL, bucket_cache
import jwt

ns = Namespace('authorize', description='Authorisation Route Namespace')

authorize_model = ns.model('Authorize', {
    'app_name': fields.String(required=True, description='Application Name'),
    'bucket_name': fields.String(required=True, description='Bucket Name'),
    'client_id': fields.String(required=True, description='Client ID')
})

token_verify_model = ns.model('TokenVerify', {
    'token': fields.String(required=True, description='Token to verify')
})

logging.basicConfig(level=LOG_LEVEL)

SECRET_KEY = environ.get("CRY_INFO", "ZGVmYXVsdF9mYWxsYmFja192YWx1ZQo=")


@ns.route('/')
class AuthoriseResource(Resource):

    @ns.expect(authorize_model, validate=True)
    @ns.doc(
        responses={
            HTTPStatus.OK: 'Token generated successfully.',
            HTTPStatus.BAD_REQUEST: 'Invalid client_id or bucket_name.',
            HTTPStatus.UNAUTHORIZED: 'Unauthorized access.',
            HTTPStatus.INTERNAL_SERVER_ERROR: 'Internal server error.'
        })
    def post(self):
        """
        Endpoint to authorize a client based on their client_id and bucket_name.
        """
        try:
            data = ns.payload
            client_id = data.get('client_id')
            bucket_name = data.get('bucket_name')
            app_name = data.get('app_name')

            # Check if the client_id and app_name + bucket_name combination is valid
            credentials = bucket_cache.get((app_name, bucket_name), None)
            if not credentials or credentials['client_id'] != client_id:
                return {'message': 'Invalid client_id or bucket_name'}, HTTPStatus.BAD_REQUEST

            token = jwt.encode({
                'client_id': client_id,
                'bucket_name': bucket_name,
                'app_name': app_name,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)  # Token expires after 1 day
            }, SECRET_KEY, algorithm='HS256')

            return {'token': token}, HTTPStatus.OK

        except Exception as e:
            logging.error(f"Error authorizing client: {str(e)}")
            return {'error': 'Internal server error'}, HTTPStatus.INTERNAL_SERVER_ERROR


@ns.route('/verify_token')
class TokenVerifyResource(Resource):

    @ns.expect(token_verify_model, validate=True)
    @ns.doc(
        responses={
            HTTPStatus.OK: 'Token is valid.',
            HTTPStatus.BAD_REQUEST: 'Invalid token format.',
            HTTPStatus.UNAUTHORIZED: 'Token is invalid or expired.',
            HTTPStatus.INTERNAL_SERVER_ERROR: 'Internal server error.'
        })
    def post(self):
        """
        Endpoint to verify if a token is still valid.
        """
        token = None  # Initialize token variable
        try:
            data = ns.payload
            token = data.get('token')

            # Utilize the verify_token function from cry_auth module
            is_valid, message = verify_token(token)

            if is_valid:
                return {'message': message}, HTTPStatus.OK
            else:
                return {'message': message}, HTTPStatus.UNAUTHORIZED

        except jwt.ExpiredSignatureError:
            logging.warning(f"Token expired for token: {token}")
            return {'message': 'Token has expired.'}, HTTPStatus.UNAUTHORIZED

        except jwt.DecodeError:
            logging.warning(f"Invalid token: {token}")
            return {'message': 'Invalid token format.'}, HTTPStatus.BAD_REQUEST

        except jwt.InvalidTokenError:
            logging.warning(f"Invalid token: {token}")
            return {'message': 'Token is invalid.'}, HTTPStatus.UNAUTHORIZED

        except Exception as e:
            logging.error(f"Error verifying token: {str(e)}")
            return {'error': 'Internal server error'}, HTTPStatus.INTERNAL_SERVER_ERROR
