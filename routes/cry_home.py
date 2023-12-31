"""
cry_home.py
-----------

Module for serving the home page of the Secrets Management Service.
This displays a list of buckets and their corresponding secrets.
"""

import logging

import keycloak
from flask import render_template, make_response, session, url_for
from flask_restx import Resource, Namespace

from globals import LOG_LEVEL, keycloak_openid, server_url, realm_name
from modules import cry_secrets_management
from modules.cry_auth_helpers import sso_required

logging.basicConfig(level=LOG_LEVEL)

ns = Namespace('crystal-secrets-manager', description='Home Route Namespace')


@ns.route('/', doc=False)  # Exclude from Swagger UI
class Home(Resource):
    """
    Resource to serve the home page. This displays a list of buckets and their corresponding secrets.
    """

    @sso_required
    def get(self):
        user_name = "Stranger"  # Default value
        login_required = False  # Flag to determine if login is required

        access_token = session.get('access_token')
        auth_url = None
        logout_redirect_endpoint = 'crystal-secrets-manager_home'
        logout_url = (f"{server_url}/auth/realms/{realm_name}/protocol/openid-connect/logout?redirect_uri="
                      f"{url_for(logout_redirect_endpoint, _external=True)}")

        if access_token:
            try:
                user_info = keycloak_openid.decode_token(access_token)
                user_name = user_info.get('name', "Stranger")
            except keycloak.exceptions.KeycloakConnectionError:
                logging.error("Failed to connect to Keycloak server. Rendering page with default user.")
                login_required = True
            except Exception as e:
                logging.warning(f"Failed to decode user info from token: {str(e)}")
                # Attempt to refresh the token if a refresh token exists in the session
    refresh_token_from_session = session.get('refresh_token')
    if refresh_token_from_session:
        new_access_token = refresh_token(refresh_token_from_session)
        if new_access_token:
            try:
                user_info = keycloak_openid.decode_token(new_access_token)
                user_name = user_info.get('name', "Stranger")
                refreshed_successfully = True
            except Exception as decode_error:
                logging.warning(f"Failed to decode user info from refreshed token: {str(decode_error)}")

    if not refreshed_successfully:
        login_required = True
        else:
            try:
                auth_url = keycloak_openid.auth_url(
                    redirect_uri=url_for('keycloak_callback_keycloak_callback', _external=True))
                login_required = True
            except keycloak.exceptions.KeycloakConnectionError:
                logging.error("Failed to connect to Keycloak server. Rendering page with default user.")
                login_required = True

        try:
            bucket_pairs = cry_secrets_management.get_buckets()
            secrets_list = {}
            for app_name, bucket_name in bucket_pairs:
                secrets_files = cry_secrets_management.get_secrets(bucket_name, app_name)
                if app_name not in secrets_list:
                    secrets_list[app_name] = {}
                secrets_list[app_name][bucket_name] = secrets_files

            version = 'cry-sec-V1.0.0'

            # Render the template with the login_required flag
            html_content = render_template('home.html',
                                           buckets=bucket_pairs,
                                           secrets=secrets_list,
                                           version=version,
                                           user_name=user_name,
                                           login_required=login_required,
                                           login_url=auth_url,
                                           logout_url=logout_url)

            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html'
            logging.info("Successfully rendered home page with list of buckets and secrets.")
            return response

        except Exception as e:
            logging.error(f"Error encountered while rendering home page: {str(e)}")
            return {'error': 'Internal server error'}, 500
