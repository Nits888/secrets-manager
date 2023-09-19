import logging
import jwt
from flask import request, jsonify, g
from flask_httpauth import HTTPTokenAuth
from jwt import InvalidTokenError

from globals import bucket_cache, LOG_LEVEL, SECRET_KEY
from modules import cry_auth_helpers

logging.basicConfig(level=LOG_LEVEL)

auth = HTTPTokenAuth(scheme='Bearer')


@auth.verify_token
def verify_token(token):
    """
    Verifies the provided JWT token.
    Args:
    - token (str): The JWT token from the incoming request.
    Returns:
    - bool: True if token validation is successful, otherwise False.
    - str: A message providing details about the validation result.
    """
    # Check if the request is for the home route
    if request.endpoint == 'home':
        return cry_auth_helpers.verify_sso_token(token)
    try:
        # Decode the token using the SECRET_KEY
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        g.bucket_name = payload.get('bucket_name', None)
        g.app_name = payload.get('app_name', None)
        chk_client_id = payload.get('client_id', None)

        if not g.bucket_name or not chk_client_id or not g.app_name:
            logging.warning("Token validation failed: Missing bucket name or client ID.")
            return False, "Bucket name or Client ID is missing in the token."

        # Fetch the client_id and client_secret associated with the bucket_name from the cache
        credentials = bucket_cache.get((g.app_name, g.bucket_name), None)
        if credentials and credentials['client_id'] == chk_client_id:
            logging.info(f"Token validation successful for client: {chk_client_id} and bucket: {g.bucket_name}.")
            return True, "Token is valid."
        else:
            logging.warning(f"Token validation failed for client: "
                            f"{chk_client_id} with provided bucket: {g.bucket_name}.")
            return False, "Invalid token or client_id doesn't match."

    except jwt.ExpiredSignatureError:
        logging.error("Token validation failed: Token has expired.")
        return False, "Token has expired."

    except InvalidTokenError:
        logging.warning("Token validation failed: Invalid token.")
        return False, "Invalid token format or structure."

    except Exception as e:
        logging.error(f"Token validation error: {str(e)}")
        return False, f"Authentication error: {str(e)}"


@auth.error_handler
def auth_error(status):
    return jsonify({'error': 'Authentication failed', 'status': status}), 401
