import secrets
import string
import random
import os
import logging
from globals import LOG_LEVEL

# Set up logging
logging.basicConfig(level=LOG_LEVEL)


def generate_password(length):
    """
    Generate a random password of the specified length.

    :param length: Length of the desired password.
    :return: Randomly generated password.
    """
    try:
        characters = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(random.choice(characters) for _ in range(length))
        return password
    except Exception as e:
        logging.error(f"Error generating password: {str(e)}")
        raise


def generate_salt():
    """
    Generate a random salt of 16 bytes (128 bits).

    :return: Randomly generated salt.
    """
    try:
        return os.urandom(16)
    except Exception as e:
        logging.error(f"Error generating salt: {str(e)}")
        raise


def generate_random_secret(length=32):
    """
    Generates a cryptographically secure random secret of a given length.

    :param length: Length of the desired secret.
    :return: Randomly generated secret.
    """
    try:
        characters = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(characters) for _ in range(length))
    except Exception as e:
        logging.error(f"Error generating random secret: {str(e)}")
        raise
