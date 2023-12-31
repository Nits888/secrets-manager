"""
cry_initialize
~~~~~~~~~~~~~~

This module provides utilities for initializing the core components of the application.
It includes functions to set up the database, create necessary directories, handle encryption keys,
and populate caches.

"""

import logging
import os
import uuid

from globals import SECRETS_DIR, BUCKET_KEYS, BUCKETS, LOG_LEVEL, bucket_cache
from modules import cry_database, cry_utils
from modules import cry_encryption

logging.basicConfig(level=LOG_LEVEL)


def initialize_app():
    """Initialize the core components of the application.

    This function performs the following tasks:
    - Set up the database connection and tables.
    - Create necessary directories for secrets.
    - Initialize the database connection pool.
    - Populate the bucket cache from the database.
    """
    logging.info("Creating Database Pool & Validating Database Pre-Requisites")
    cry_database.create_table()
    _create_directory_if_not_exists(SECRETS_DIR, "Creating Secrets Directory as it's missing")
    cry_database.create_dml_connection_pool()
    logging.info("Initializing Buckets Cache from Database")
    initialize_bucket_cache()


def _create_directory_if_not_exists(directory_path, log_message=None):
    """Create a directory if it doesn't exist.

    Args:
        directory_path (str): Path of the directory to check/create.
        log_message (str, optional): Message to log if the directory is missing. Defaults to None.

    Returns:
        str: The path of the directory.
    """
    if not os.path.exists(directory_path):
        if log_message:
            logging.info(log_message)
        os.makedirs(directory_path)
    return directory_path


def _handle_missing_key(bucket_name, key_salt_file_path):
    """
    Handle the case where the encryption key and salt for a bucket is missing.

    Generate a new key and salt, save them to the specified file, and backup to the database.

    Parameters:
    - bucket_name (str): Name of the bucket for which key and salt are missing.
    - key_salt_file_path (str): Path where the new key and salt should be saved.
    """
    new_key = cry_encryption.generate_key()
    new_salt = cry_utils.generate_salt()

    # Convert them to string representation for combination
    new_key_str = new_key.decode('utf-8')
    new_salt_str = new_salt.decode('utf-8')

    # Combine key and salt
    combined_key_salt = f"{new_key_str}${new_salt_str}"

    BUCKET_KEYS[bucket_name]['encryption_key'] = new_key
    with open(key_salt_file_path, 'wb') as combined_file:
        combined_file.write(combined_key_salt.encode('utf-8'))

    client_id = str(uuid.uuid4())
    try:
        cry_database.backup_keys(bucket_name, combined_key_salt, client_id)
    except Exception as e:
        logging.error(f"Error while creating bucket: {str(e)}")
        return {'message': 'Failed to create bucket.'}, 500


def create_bucket_directories_keys():
    """
    Create directories for each app and bucket and handle the associated encryption keys.

    For each app and its buckets, ensure that the directories exist and then manage its encryption key.
    """
    for app_name, bucket_dict in BUCKETS.items():
        app_path = _create_directory_if_not_exists(os.path.join(SECRETS_DIR, app_name),
                                                   f"Creating App Directory for: {app_name}")
        for bucket_name in bucket_dict.keys():
            bucket_path = _create_directory_if_not_exists(os.path.join(app_path, bucket_name),
                                                          f"Creating Bucket Directory for: {bucket_name}")
            key_file_path = os.path.join(bucket_path, 'secret.key')
            if not os.path.exists(key_file_path):
                encryption_key = BUCKET_KEYS.get(app_name, {}).get(bucket_name, {}).get('encryption_key')
                if encryption_key is None:
                    _handle_missing_key(bucket_name, key_file_path)
                else:
                    _write_existing_key_to_file(bucket_name, key_file_path, encryption_key)


def initialize_buckets(app_bucket_keys_list):
    """
    Initialize apps and buckets with their associated encryption keys.

    Parameters:
    - app_bucket_keys_list (list): List of tuples containing app names, bucket names and their associated encryption keys.
    """
    for app_name, bucket_name, encryption_key in app_bucket_keys_list:
        if app_name not in BUCKETS:
            BUCKETS[app_name] = {}
        BUCKETS[app_name][bucket_name] = []

        if app_name not in BUCKET_KEYS:
            BUCKET_KEYS[app_name] = {}
        BUCKET_KEYS[app_name][bucket_name] = {'encryption_key': encryption_key}

    create_bucket_directories_keys()


def _write_existing_key_to_file(bucket_name, key_file_path, encryption_key):
    """
    Write an existing encryption key to the specified file.

    Parameters:
    - bucket_name (str): Name of the bucket for the key.
    - key_file_path (str): Path to the file where the key should be written.
    - encryption_key (str): The encryption key to write.
    """
    if isinstance(encryption_key, str):
        try:
            encryption_key = bytes.fromhex(encryption_key)
        except ValueError:
            logging.error(
                f"Invalid key format for bucket '{bucket_name}'. The encryption key must be a valid hex string.")
            return
    with open(key_file_path, "wb") as key_file:
        key_file.write(encryption_key)


def initialize_secrets_from_db():
    """
    Fetch all secrets from the database and create the necessary files on the system for each secret.
    """
    secrets = cry_database.get_all_secrets()
    for secret in secrets:
        app_name, bucket_name, secret_name, encrypted_secret = secret  # Adjusted to receive app_name
        app_directory = os.path.join("secrets", app_name)
        _create_directory_if_not_exists(app_directory)  # Ensure app directory exists
        bucket_directory = os.path.join(app_directory, bucket_name)  # Adjusted to nest bucket inside app directory
        _create_directory_if_not_exists(bucket_directory)
        secret_file_path = os.path.join(bucket_directory, f"{secret_name}.json")
        if not os.path.exists(secret_file_path):
            with open(secret_file_path, "wb") as secret_file:
                secret_file.write(encrypted_secret)


def refresh_bucket_cache():
    """
    Refresh the bucket cache to ensure it contains all apps and buckets from the database.
    """
    # Step 1: Get the current list of apps and buckets from the database
    current_buckets = cry_database.get_all_buckets()

    # Step 2: Compare it with the cache to identify any missing apps or buckets
    for bucket in current_buckets:
        app_name, bucket_name, _, client_id = bucket
        if (app_name, bucket_name) not in bucket_cache:
            # Step 3: Add the missing apps or buckets to the cache
            bucket_cache[app_name, bucket_name] = {'client_id': client_id}
            logging.info(f"Added missing app '{app_name}' and bucket '{bucket_name}' to the cache")


def initialize_bucket_cache():
    """Populate a cache of bucket details fetched from the database.

    Returns:
        dict: A dictionary with bucket names as keys and their details (client_id and client_secret) as values.
    """
    all_buckets = cry_database.get_all_buckets()
    # bucket_cache = {}
    for bucket in all_buckets:
        app_name, bucket_name, _, client_id = bucket
        bucket_cache[app_name, bucket_name] = {'client_id': client_id}
    return bucket_cache
