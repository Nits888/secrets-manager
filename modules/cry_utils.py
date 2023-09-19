"""
cry_utils
~~~~~~~~~

This module provides utility functions for generating cryptographically secure random passwords, salts, and secrets.
"""

import secrets
import string
import os
import logging
from globals import LOG_LEVEL

# Set up logging
logging.basicConfig(level=LOG_LEVEL)


def generate_password(length):
    """
    Generate a cryptographically secure random password of the specified length.

    :param int length: Length of the desired password.
    :return: Randomly generated password.
    :rtype: str
    :raises Exception: If there's an error generating the password.
    """
    try:
        characters = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(secrets.choice(characters) for _ in range(length))
        return password
    except Exception as e:
        logging.error(f"Error generating password: {str(e)}")
        raise


def generate_salt():
    """
    Generate a random salt of 16 bytes (128 bits).

    :return: Randomly generated salt.
    :rtype: bytes
    :raises Exception: If there's an error generating the salt.
    """
    try:
        return os.urandom(16)
    except Exception as e:
        logging.error(f"Error generating salt: {str(e)}")
        raise


def generate_random_secret(length=32):
    """
    Generates a cryptographically secure random secret of a given length.

    :param int length: Length of the desired secret. Default is 32.
    :return: Randomly generated secret.
    :rtype: str
    :raises Exception: If there's an error generating the secret.
    """
    try:
        characters = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(characters) for _ in range(length))
    except Exception as e:
        logging.error(f"Error generating random secret: {str(e)}")
        raise
