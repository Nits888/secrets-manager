"""
cry_auth_helpers
~~~~~~~~~~~~~~~~

This module provides helper functions for Single Sign-On (SSO) authentication,
IP whitelisting, and JWT token operations.

"""

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
    """Decorator to ensure Single Sign-On (SSO) authentication.

    Args:
        func (function): The function to be decorated.

    Returns:
        function: The decorated function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # Check if the session contains an access token for SSO
            access_token = session.get('access_token')
            if not access_token:
                logging.warning("No access token found in session.")

            if not access_token or not verify_sso_token(access_token):
                # If no valid access token is found, redirect to Keycloak login
                auth_url = keycloak_openid.auth_url(redirect_uri=url_for('keycloak_callback_keycloak_callback',
                                                                         _external=True))
                return redirect(auth_url)

            return func(*args, **kwargs)

        except KeycloakConnectionError:
            logging.error("Failed to connect to Keycloak server. Rendering page with default user.")
            g.user = "Welcome User"  # Set a default user value in the Flask global object
            return func(*args, **kwargs)

        except Exception as e:
            logging.error(f"Unexpected error in sso_required decorator: {str(e)}")
            return {"error": "Internal server error."}, 500  # 500 Internal Server Error

    return wrapper


def verify_sso_token(token):
    """Verifies the SSO token using Keycloak.

    Args:
        token (str): The SSO token to be verified.

    Returns:
        bool: True if the token is active, False otherwise.
    """
    try:
        token_info = keycloak_openid.introspect(token)
        if token_info.get('active'):
            return True, "Token is valid."
        else:
            logging.warning("SSO token is not active.")
            return False, "Token is invalid."
    except Exception as e:
        logging.error(f"SSO token validation error: {str(e)}")
        return False, "Token is invalid."


def ip_whitelist_required(f):
    """Decorator to check if the incoming IP is whitelisted.

     Args:
         f (function): The function to be decorated.

     Returns:
         function: The decorated function.
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
        return {'error': 'Unauthorized IP address'}, 403  # Return the dictionary directly

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
