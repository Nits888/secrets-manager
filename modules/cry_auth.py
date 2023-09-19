import logging
from functools import wraps
from os import environ

import jwt
from flask import request, jsonify, g, session, redirect, url_for
from flask_httpauth import HTTPTokenAuth
from jwt import InvalidTokenError
from keycloak import KeycloakConnectionError

from globals import bucket_cache, LOG_LEVEL, keycloak_openid
from routes.cry_create_bucket import get_bucket_config

logging.basicConfig(level=LOG_LEVEL)

# Fetch SECRET_KEY from environment variable CRY_INFO
SECRET_KEY = environ.get("CRY_INFO", "UGFwcHVDYW50RGFuY2VTYWFsYUAyMDIwMzEjJCUK")

auth = HTTPTokenAuth(scheme='Bearer')


def sso_required(func):
    """
    Decorator to ensure Single Sign-On (SSO) authentication.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Check if the session contains an access token for SSO
        access_token = session.get('access_token')
        if not access_token or not verify_sso_token(access_token):
            try:
                # If no valid access token is found, redirect to Keycloak login
                auth_url = keycloak_openid.auth_url(redirect_uri=url_for('keycloak_callback_keycloak_callback',
                                                                         _external=True))
                return redirect(auth_url)
            except KeycloakConnectionError:
                logging.error("Failed to connect to Keycloak server. Rendering page with default user.")
                g.user = "Welcome User"  # Set a default user value in the Flask global object
        return func(*args, **kwargs)

    return wrapper


def verify_sso_token(token):
    """
    Verifies the SSO token using Keycloak.
    """
    try:
        token_info = keycloak_openid.introspect(token)
        if token_info.get('active'):
            return True
        else:
            logging.warning("SSO token is not active.")
            return False
    except Exception as e:
        logging.error(f"SSO token validation error: {str(e)}")
        return False


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
    # Check if the request is for the home route
    if request.endpoint == 'home':
        return verify_sso_token(token)
    try:
        # Decode the token using the SECRET_KEY
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        g.bucket_name = payload.get('bucket_name', None)  # Set the bucket name early
        g.app_name = payload.get('app_name', None)  # Set the app name early
        chk_client_id = payload.get('client_id', None)

        if not g.bucket_name or not chk_client_id or not g.app_name:
            logging.warning("Token validation failed: Missing bucket name or client ID.")
            return False, "Bucket name or Client ID is missing in the token."

        # Check the IP whitelist
        incoming_ip = request.remote_addr
        bucket_config = get_bucket_config(g.bucket_name, g.app_name)
        allowed_ips = bucket_config.get("allowed_ips", [])
        if incoming_ip not in allowed_ips:
            logging.warning(f"Unauthorized IP address attempt: {incoming_ip} for bucket {g.bucket_name}.")
            return False, "Unauthorized IP address."

        # Fetch the client_id and client_secret associated with the bucket_name from the cache
        credentials = bucket_cache.get((g.app_name, g.bucket_name), None)
        logging.info(str(credentials))
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


def ip_whitelist_required(f):
    """
    Decorator to check if the incoming IP is whitelisted.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Retrieve the client IP from the X-Real-IP header
        incoming_ip = request.headers.get('X-Real-IP', request.remote_addr)
        bucket_config = get_bucket_config(g.bucket_name, g.app_name)
        allowed_ips = bucket_config.get("allowed_ips", [])

        # If "ANY" is in the allowed_ips list or the incoming IP is in the allowed_ips list, allow the request
        if "ANY" in allowed_ips:
            logging.info(f"IP address {incoming_ip} allowed due to 'ANY' in whitelist for bucket {g.bucket_name}.")
            return f(*args, **kwargs)
        elif incoming_ip in allowed_ips:
            return f(*args, **kwargs)

        logging.warning(f"Unauthorized IP address attempt: {incoming_ip} for bucket {g.bucket_name}.")
        return jsonify({'error': 'Unauthorized IP address'}), 403

    return decorated_function


@auth.error_handler
def auth_error(status):
    return jsonify({'error': 'Authentication failed', 'status': status}), 401
