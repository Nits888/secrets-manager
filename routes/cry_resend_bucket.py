import logging
from http import HTTPStatus

from flask import request
from flask_restx import Namespace, Resource, fields

from globals import LOG_LEVEL, bucket_cache
from modules import cry_email_sender
from routes.cry_create_bucket import get_bucket_config

ns = Namespace('resend_bucket_details', description='Bucket Management Route Namespace')

bucket_model = ns.model('Bucket', {
    'app_name': fields.String(required=True, description='Application Name'),
    'bucket': fields.String(required=True, description='Bucket name'),
})

logging.basicConfig(level=LOG_LEVEL)


@ns.route('/')
class ResendBucketDetailsResource(Resource):

    @ns.expect(bucket_model, validate=True)
    @ns.doc(
        responses={
            HTTPStatus.OK: 'Bucket details resent successfully.',
            HTTPStatus.BAD_REQUEST: 'Invalid bucket name or bucket does not exist.',
            HTTPStatus.UNAUTHORIZED: 'Unauthorized access.',
            HTTPStatus.INTERNAL_SERVER_ERROR: 'Internal server error.'
        })
    def post(self):
        """
        Resend bucket details.

        The incoming IP address is checked against allowed IPs from the bucket's configuration.
        """
        try:
            data = ns.payload
            bucket_name = data.get('bucket')
            app_name = data.get('app_name')

            logging.info(f"Incoming request to resend details for bucket: {bucket_name} from IP: {request.remote_addr}")

            # Load specific bucket config
            bucket_config = get_bucket_config(bucket_name, app_name)

            if not bucket_config:
                logging.warning(f"Bucket configuration not found for: {bucket_name}")
                return {'message': 'Bucket configuration not found or bucket name not allowed'}, HTTPStatus.BAD_REQUEST

            allowed_ips = bucket_config.get("allowed_ips", [])

            # Check IP address
            if request.remote_addr not in allowed_ips:
                return {'message': 'Unauthorized IP address'}, HTTPStatus.UNAUTHORIZED

            return resend_bucket_details(bucket_name, app_name)

        except Exception as e:
            logging.error(f"Error resending bucket details: {str(e)}")
            return {'error': 'Internal server error'}, HTTPStatus.INTERNAL_SERVER_ERROR


def resend_bucket_details(bucket_name, app_name):
    """
    Helper function to resend details for an existing bucket.

    Args:
        bucket_name (str): The name of the bucket.
        app_name (str) : Application Name for the Bucket.
    Returns:
        tuple: A tuple containing a response message and a HTTP status code.
    """
    # Fetch the client_id from the cache
    bucket_data = bucket_cache.get((app_name, bucket_name))
    client_id = bucket_data.get('client_id') if bucket_data else None

    if client_id:
        # Get owner's email from bucket config
        bucket_config = get_bucket_config(bucket_name, app_name)
        owner_email = bucket_config.get('owner_email', None)

        if owner_email:
            email_subject = f"Details for Bucket '{bucket_name}'"
            email_body = f"Your client ID for bucket '{bucket_name}' is {client_id}."
            cry_email_sender.send_email(email_subject, email_body, owner_email)
        else:
            logging.warning("owner_email missing in config, No E-Mail Sent")
            return {
                'message': f"Details for {bucket_name} retrieved successfully. "
                           f"Owner_Email Missing in Configuration - E-Mail Not Sent"
            }, HTTPStatus.OK

        logging.info(f"Details for {bucket_name} resent successfully.")
        return {
            'message': f"Details for bucket '{bucket_name}' resent successfully.",
            'client_id': client_id,
        }, HTTPStatus.OK
    else:
        return {
            'message': f"Failed to retrieve details for bucket '{bucket_name}'. Ensure the name is valid and exists."
        }, HTTPStatus.BAD_REQUEST
