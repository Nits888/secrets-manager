from flask_restx import Namespace, Resource, fields
from http import HTTPStatus
import logging
import json
import os

from modules import cry_secrets_management, cry_email_sender
from globals import LOG_LEVEL, server_env
from flask import request


ns = Namespace('create_bucket', description='Bucket Management Route Namespace')

bucket_model = ns.model('Bucket', {
    'app_name': fields.String(required=True, description='Application Name'),
    'bucket': fields.String(required=True, description='Bucket name'),
})

logging.basicConfig(level=LOG_LEVEL)


def get_bucket_config(bucket_name, app_name):
    """
    Load the bucket-specific configuration by searching through the 'config' directory and its subdirectories.

    Args:
        bucket_name (str): The name of the bucket.
        app_name (str) : Application Name for the Bucket.

    Returns:
        dict: Configuration data for the bucket or None if not found.
    """
    config_dir = os.path.join('config', server_env, app_name)
    for root, dirs, files in os.walk(config_dir):
        if f"{bucket_name}.json" in files:
            config_path = os.path.join(root, f"{bucket_name}.json")
            with open(config_path, 'r') as config_file:
                config = json.load(config_file)
            return config

    return None


@ns.route('/')
class BucketResource(Resource):

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

            allowed_ips = bucket_config.get("allowed_ips", [])

            # Check IP address
            if request.remote_addr not in allowed_ips:
                return {'message': 'Unauthorized IP address'}, HTTPStatus.UNAUTHORIZED

            return create_bucket(bucket_name, app_name)

        except Exception as e:
            logging.error(f"Error creating bucket: {str(e)}")
            return {'error': 'Internal server error'}, HTTPStatus.INTERNAL_SERVER_ERROR


def create_bucket(bucket_name, app_name):
    """
    Helper function to create a new bucket.

    Args:
        bucket_name (str): The name of the bucket to be created.
        app_name (str) : Application Name for the Bucket.
    Returns:
        tuple: A tuple containing a response message and a HTTP status code.
    """
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
