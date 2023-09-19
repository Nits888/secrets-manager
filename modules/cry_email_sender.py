"""
cry_email_sender
~~~~~~~~~~~~~~~~

This module provides a utility to send emails using an external email sender API.
It uses the `requests` library to make a POST request to the email sender API.

"""

import requests
import logging

from globals import LOG_LEVEL

logging.basicConfig(level=LOG_LEVEL)

EMAIL_SENDER_API_URL = "https://your-email-api-url/send"  # Replace with your email sender API URL
API_KEY = "YOUR_API_KEY"  # If your API requires an authentication key


def send_email(subject, message_body, recipient_email):
    """Send an email using the external email sender API.

    This function constructs a payload with the email details and sends a POST request
    to the email sender API. It logs the result of the email sending operation.

    Args:
        subject (str): The subject of the email.
        message_body (str): The body of the email.
        recipient_email (str): The email address of the recipient.

    Returns:
        None

    Raises:
        Exception: If there's an error during the API request.
    """
    try:
        # Construct the payload
        payload = {
            "subject": subject,
            "message": message_body,
            "recipient": recipient_email
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"  # If your API requires an authentication key
        }

        response = requests.post(EMAIL_SENDER_API_URL, json=payload, headers=headers)

        if response.status_code == 200:
            logging.info(f"Email sent successfully to {recipient_email} with subject: {subject}")
        else:
            logging.error(f"Failed to send email. API Response: {response.text}")

    except Exception as e:
        logging.error(f"Error sending email: {str(e)}")
