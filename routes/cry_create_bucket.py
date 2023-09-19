"""
cry_create_bucket.py
--------------------

Module for creating a new bucket in the secrets management system.
"""

import logging
from http import HTTPStatus

from flask import request, session, url_for, redirect, g
from flask_restx import Namespace, Resource, fields
from keycloak import KeycloakConnectionError

from globals import LOG_LEVEL, keycloak_openid
from modules import cry_secrets_management, cry_email_sender
from modules.cry_auth_helpers import verify_sso_token, get_user_email_from_token
from modules.cry_secrets_management import get_bucket_config

ns = Namespace('create_bucket', description='Bucket Management Route Namespace')

# Define a model for the data payload
bucket_model = ns.model('Bucket', {
    'app_name': fields.String(required=True, description='Application Name'),
    'bucket': fields.String(required=True, description='Bucket name'),
})

logging.basicConfig(level=LOG_LEVEL)


def create_bucket(bucket_name, app_name):
    """
    Helper function to create a new bucket.

    Args:
        bucket_name (str): The name of the bucket to be created.
        app_name (str): Application Name for the Bucket.

    Returns:
        tuple: A tuple containing a dictionary with the result message and an HTTP status code.
    """
    # Function implementation here
    success, client_id = cry_secrets_management.create_bucket(bucket_name, app_name)
    if success:
        # Get owner's email from bucket config
        bucket_config = get_bucket_config(bucket_name, app_name)
        owner_email = bucket_config.get('owner_email', None)

        if owner_email:
            email_subject = f"New Bucket '{bucket_name}' Created"
            email_body = f"The bucket '{bucket_name}' was successfully created. Your client ID is {client_id}."
            cry_email_sender.send_email(email_subject, email_body, owner_email)
        else:
            logging.warning("owner_email missing in config, No E-Mail Sent")
            return {
                'message': f"{bucket_name} Created Successfully for Request from IP: {request.remote_addr}. "
                           f"Owner_Email Missing in Configuration - E-Mail Not Sent"
            }, HTTPStatus.OK

        logging.info(f"{bucket_name} Created Successfully for Request from IP: {request.remote_addr}")
        return {
            'message': f"Bucket '{bucket_name}' created successfully.",
            'client_id': client_id,
        }, HTTPStatus.OK
    else:
        return {
            'message': f"Failed to create bucket '{bucket_name}'. Ensure the name is valid and doesn't already exist."
        }, HTTPStatus.BAD_REQUEST


@ns.route('/')
class BucketResource(Resource):
    """
    Resource for creating a new bucket.
    """

    @ns.expect(bucket_model, validate=True)
    @ns.doc(
        responses={
            HTTPStatus.OK: 'Bucket created successfully.',
            HTTPStatus.BAD_REQUEST: 'Invalid bucket name or bucket already exists.',
            HTTPStatus.UNAUTHORIZED: 'Unauthorized access.',
            HTTPStatus.INTERNAL_SERVER_ERROR: 'Internal server error.'
        })
    def post(self):
        """
        Create a bucket.

        The incoming IP address is checked against allowed IPs from the bucket's configuration.

        :return: A response indicating the result of the bucket creation.
        """
        try:
            data = ns.payload
            bucket_name = data.get('bucket')
            app_name = data.get('app_name')

            logging.info(f"Incoming request to create bucket: {bucket_name} from IP: {request.remote_addr}")

            # Check if the bucket already exists before loading its config
            if cry_secrets_management.bucket_exists(bucket_name, app_name):
                return {'message': f"Bucket '{bucket_name}' already exists"}, HTTPStatus.BAD_REQUEST

            # Load specific bucket config
            bucket_config = get_bucket_config(bucket_name, app_name)

            if not bucket_config:
                logging.warning(f"Bucket configuration not found for: {bucket_name}")
                return {'message': 'Bucket configuration not found or bucket name not allowed'}, HTTPStatus.BAD_REQUEST

            # Check if the request is coming from the home endpoint
            if request.endpoint == 'crystal-secrets-manager_home':
                # Verify SSO token and get email from access_token
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

                if access_token and access_token.startswith('Bearer '):
                    access_token = access_token[len('Bearer '):]  # Remove the 'Bearer ' prefix

                # Get user email from the access token
                user_email = get_user_email_from_token(access_token)

                # Get owner email from bucket config
                owner_email = bucket_config.get('owner_email', None)

                # Split owner_email into a list of emails, assuming it's a comma-separated string
                owner_emails = owner_email.split(',') if owner_email else []

                # Check if user_email exists in the list of owner_emails
                if user_email and user_email in owner_emails:
                    return create_bucket(bucket_name, app_name)
                else:
                    logging.warning("Unauthorized access: User email does not match any of the bucket owner's emails.")
                    return ({
                                'message': 'Unauthorized access: User email does not match any of the bucket owner\'s '
                                           'emails.'},
                            HTTPStatus.UNAUTHORIZED)
            else:
                # For other endpoints, apply the ip_whitelist_required decorator
                return create_bucket(bucket_name, app_name)

        except Exception as e:
            logging.error(f"Error creating bucket: {str(e)}")
            return {'error': 'Internal server error'}, HTTPStatus.INTERNAL_SERVER_ERROR
