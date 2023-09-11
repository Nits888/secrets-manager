import logging
from os import environ
import jwt

from jwt import InvalidTokenError

from flask import request, jsonify, g
from flask_httpauth import HTTPTokenAuth

from globals import bucket_cache, LOG_LEVEL
from routes.cry_create_bucket import get_bucket_config

logging.basicConfig(level=LOG_LEVEL)

# Fetch SECRET_KEY from environment variable CRY_INFO
SECRET_KEY = environ.get("CRY_INFO", "UGFwcHVDYW50RGFuY2VTYWFsYUAyMDIwMzEjJCUK")

auth = HTTPTokenAuth(scheme='Bearer')


@auth.verify_token
def verify_token(token):
    """
    Verifies the provided JWT token and validates the IP whitelist for the corresponding bucket.
    Args:
    - token (str): The JWT token from the incoming request.
    Returns:
    - bool: True if token and IP validation are successful, otherwise False.
    - str: A message providing details about the validation result.
    """
    try:
        # Decode the token using the SECRET_KEY
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        g.bucket_name = payload.get('bucket_name', None)  # Set the bucket name early
        client_id = payload.get('client_id', None)

        if not g.bucket_name or not client_id:
            logging.warning("Token validation failed: Missing bucket name or client ID.")
            return False, "Bucket name or Client ID is missing in the token."

        # Check the IP whitelist
        incoming_ip = request.remote_addr
        bucket_config = get_bucket_config(g.bucket_name)  # Assume this function exists and fetches the bucket's config
        allowed_ips = bucket_config.get("allowed_ips", [])
        if incoming_ip not in allowed_ips:
            logging.warning(f"Unauthorized IP address attempt: {incoming_ip} for bucket {g.bucket_name}.")
            return False, "Unauthorized IP address."

        # Fetch the client_id and client_secret associated with the bucket_name from the cache
        credentials = bucket_cache.get(g.bucket_name, None)
        if credentials and credentials['client_id'] == client_id:
            logging.info(f"Token validation successful for client: {client_id} and bucket: {g.bucket_name}.")
            return True, "Token is valid."
        else:
            logging.warning(f"Token validation failed for client: {client_id} with provided bucket: {g.bucket_name}.")
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
