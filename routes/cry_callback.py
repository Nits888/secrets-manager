import logging

from flask import request, url_for, redirect, session, jsonify
from flask_restx import Resource, Namespace

from globals import LOG_LEVEL, keycloak_openid

logging.basicConfig(level=LOG_LEVEL)

ns = Namespace('keycloak_callback', description='KeyCloak Callback Namespace')


@ns.route('/callback', doc=False)
class KeycloakCallback(Resource):
    """
    Keycloak Callback Resource
    --------------------------

    ...

    """

    @staticmethod
    def get():
        """
        Handle the GET request from Keycloak's redirect.

        Returns
        -------
        Response
            Redirects to the home route after successfully storing the access token in the session.
        """

        try:
            # Retrieve the authorization code from the query parameters
            code = request.args.get('code')
            if not code:
                logging.warning("Authorization code not provided in callback.")
                return jsonify({'error': 'Authorization code missing'}), 400

            # Define the callback URL
            callback_url = url_for('keycloak_callback_keycloak_callback', _external=True)

            # Exchange the authorization code for an access token
            token_response = keycloak_openid.token(
                grant_type='authorization_code',
                code=code,
                redirect_uri=callback_url
            )

            # Check if the token response contains an error
            if 'error' in token_response:
                logging.error(f"Error during token exchange: {token_response['error_description']}")
                return jsonify({'error': token_response['error_description']}), 400

            access_token = token_response.get('access_token')
            if not access_token:
                logging.error("Access token not found in token response.")
                return jsonify({'error': 'Access token missing in response'}), 500

            # Store the access token in the session
            session['access_token'] = access_token
            logging.info("Access token successfully stored in session.")

            # Redirect to the home route
            return redirect(url_for('Home'))

        except Exception as e:
            logging.error(f"Error encountered during Keycloak callback: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
