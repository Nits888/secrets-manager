import logging
from functools import wraps


import jwt
from flask import request, jsonify, g, session, redirect, url_for
from flask_httpauth import HTTPTokenAuth

from keycloak import KeycloakConnectionError

from globals import LOG_LEVEL, keycloak_openid, SECRET_KEY
from modules.cry_secrets_management import get_bucket_config

logging.basicConfig(level=LOG_LEVEL)

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


def get_user_email_from_token(access_token):
    """
    Extracts the user email from the JWT token.

    Args:
    - access_token (str): The JWT token to extract user email from.

    Returns:
    - str: The user's email if found in the token, otherwise None.
    """
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=['HS256'])
        user_email = payload.get('email')
        return user_email
    except jwt.ExpiredSignatureError:
        # Handle token expiration error if needed
        pass
    except jwt.DecodeError:
        # Handle token decode error if needed
        pass
    return None
