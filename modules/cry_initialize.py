import base64
import logging
import os
import uuid

from globals import SECRETS_DIR, BUCKET_KEYS, BUCKETS
from modules import cry_database
from modules import cry_encryption


def initialize_app():
    # Create Pool & Database
    logging.info("Creating Database Pool & Validating Database Pre-Requisites")
    cry_database.create_table()
    # Create the 'secrets' directory if it doesn't exist
    if not os.path.exists(SECRETS_DIR):
        logging.info("Creating Secrets Directory as it's missing")
        os.makedirs(SECRETS_DIR)
    # Creating Database Connection pool
    cry_database.create_connection_pool()
    # Initialize buckets and keys from the database if missing
    # logging.info("Initializing Buckets & Keys from Database")
    # bucket_keys_list = initialize_buckets_and_keys_from_db()
    # initialize_buckets(bucket_keys_list)
    # logging.info("Initializing Secrets from Database")
    # initialize_secrets_from_db()
    # Creating Bucket Cache
    logging.info("Initializing Buckets Cache from Database")
    initialize_bucket_cache()


def create_bucket_directories_keys():
    # Create directories for each bucket if they are missing
    for bucket_name in BUCKETS:
        bucket_path = os.path.join(SECRETS_DIR, bucket_name)
        if not os.path.exists(bucket_path):
            logging.info("Creating Bucket Directory for : " + bucket_name)
            os.makedirs(bucket_path)
        key_file_path = os.path.join(bucket_path, 'secret.key')
        if not os.path.exists(key_file_path):
            # If 'secret.key' file is missing, get the key from the BUCKET_KEYS dictionary
            encryption_key = BUCKET_KEYS.get(bucket_name, {}).get('encryption_key')
            if encryption_key is None:
                # If the key is not available in BUCKET_KEYS, generate a new key and save it
                new_key = cry_encryption.generate_key()
                BUCKET_KEYS[bucket_name]['encryption_key'] = new_key
                # Save to Database
                client_id = str(uuid.uuid4())
                client_secret = base64.urlsafe_b64encode(os.urandom(16)).decode('utf-8')
                with open(key_file_path, 'wb') as key_file:
                    key_file.write(new_key)  # Write the bytes key to the file
                # Backup the key to the database
                try:
                    cry_database.backup_keys(bucket_name, new_key, client_id, client_secret)
                except Exception as e:
                    print(f"Error while creating bucket: {str(e)}")
                    return {'message': 'Failed to create bucket.'}, 500
            else:
                # If the key is available in BUCKET_KEYS, convert it to bytes and create the 'secret.key' file
                # bytes_key = encryption_key.hex()
                # logging.info(encryption_key)
                # Convert the encryption key to bytes if it's in hex format
                if isinstance(encryption_key, str):
                    try:
                        encryption_key = bytes.fromhex(encryption_key)
                    except ValueError:
                        # Handle the ValueError gracefully
                        print(
                            f"Invalid key format for bucket '{bucket_name}'. The encryption key must be a valid hex"
                            f"string.")
                        continue
                with open(key_file_path, "wb") as key_file:
                    key_file.write(encryption_key)


def initialize_buckets(bucket_keys_list):
    # Initialize the BUCKETS and BUCKET_KEYS dictionaries using the combined list
    for bucket_name, encryption_key in bucket_keys_list:
        BUCKETS[bucket_name] = []
        BUCKET_KEYS[bucket_name] = {
            'encryption_key': encryption_key,
        }
    create_bucket_directories_keys()


def initialize_secrets_from_db():
    # Get the list of secrets from the database
    secrets = cry_database.get_all_secrets()
    # Create secret files if missing
    for secret in secrets:
        bucket_name, secret_name, encrypted_secret = secret
        bucket_directory = os.path.join("secrets", bucket_name)
        if not os.path.exists(bucket_directory):
            os.makedirs(bucket_directory)
        secret_file_path = os.path.join(bucket_directory, f"{secret_name}.json")
        if not os.path.exists(secret_file_path):
            # Write the encrypted_secret to the secret file
            with open(secret_file_path, "wb") as secret_file:
                secret_file.write(encrypted_secret)


def initialize_bucket_cache():
    # Fetch all buckets with their client_id and client_secret from the database
    all_buckets = cry_database.get_all_buckets()

    # Create a dictionary to store bucket details in memory
    bucket_cache = {}
    for bucket in all_buckets:
        bucket_name, _, client_id, client_secret = bucket
        bucket_cache[bucket_name] = {
            'client_id': client_id,
            'client_secret': client_secret
        }

    return bucket_cache
