import base64
import os
import uuid
import logging

from globals import bucket_cache, SECRETS_DIR, SECRET_KEY_FILE
from modules import cry_database
from modules import cry_encryption
from modules import cry_utils

# Initialize the logger for this module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BucketError(Exception):
    """Exception raised for errors related to bucket operations."""
    pass


class SecretError(Exception):
    """Exception raised for errors related to secret operations."""
    pass


def _read_key_salt_from_file(bucket):
    """Internal utility to read the key and salt from the bucket's files."""
    secret_master_key_path = os.path.join(SECRETS_DIR, bucket, SECRET_KEY_FILE)

    if not os.path.exists(secret_master_key_path):
        logger.error(f"Combined Key or Salt file not found for bucket '{bucket}'.")
        raise BucketError(f"Combined Key or Salt file not found for bucket '{bucket}'.")

    with open(secret_master_key_path, 'rb') as key_salt_file:
        combined_key_salt = key_salt_file.read().decode('utf-8')
        key_str, salt_str = combined_key_salt.split('$')  # Assuming '$' is the delimiter
        key = base64.b64decode(key_str.encode('utf-8'))
        salt = base64.b64decode(salt_str.encode('utf-8'))

    return key, salt


def _get_secret_file_path(bucket, service_name):
    """Return the file path for a given secret within a bucket."""
    return os.path.join(SECRETS_DIR, bucket, f"{service_name}.json")


def bucket_exists(bucket):
    """Check if the specified bucket exists."""
    return os.path.exists(os.path.join(SECRETS_DIR, bucket))


def create_bucket(bucket):
    """Create a new secrets bucket with associated key and salt."""
    if not bucket_exists(bucket):
        # Generate a new key and salt for the bucket
        key = cry_encryption.generate_key()
        salt = cry_utils.generate_salt()
        client_id = str(uuid.uuid4())

        # Convert the generated key and salt to base64 encoded strings
        key_str = base64.b64encode(key).decode('utf-8')
        salt_str = base64.b64encode(salt).decode('utf-8')

        # Combine key and salt
        combined_key_salt = f"{key_str}${salt_str}"  # Using '$' as delimiter for this example.

        try:
            cry_database.backup_keys(bucket, combined_key_salt, client_id)
        except Exception as e:
            logging.error(f"Error while creating bucket: {str(e)}")
            raise BucketError('Failed to create bucket.')

        os.makedirs(os.path.join(SECRETS_DIR, bucket))

        # Write the combined key and salt in binary format
        with open(os.path.join(SECRETS_DIR, bucket, SECRET_KEY_FILE), 'wb') as combined_file:
            combined_file.write(combined_key_salt.encode('utf-8'))

        bucket_cache[bucket] = {
            'client_id': client_id,
        }
        return True, client_id
    else:
        logging.error("Attempted to create an already existing bucket.")
        raise BucketError('Bucket already exists.')


def secret_exists(bucket, service_name):
    """Check if a secret associated with a service name exists within a bucket."""
    return os.path.exists(_get_secret_file_path(bucket, service_name))


def store_secret(bucket, service_name, secret):
    """Store an encrypted secret within a specified bucket and service name."""
    secret_path = _get_secret_file_path(bucket, service_name)
    key, salt = _read_key_salt_from_file(bucket)
    if isinstance(secret, bytes):
        secret = secret.decode()
    encrypted_secret = cry_encryption.encrypt_string(secret, salt)
    cry_database.save_secret(bucket, service_name, encrypted_secret)
    with open(secret_path, 'wb') as secret_file:
        secret_file.write(encrypted_secret)


def retrieve_secret(bucket, service_name):
    """Retrieve and decrypt a secret from the specified bucket and service name."""
    secret_path = _get_secret_file_path(bucket, service_name)
    if not os.path.exists(secret_path):
        raise SecretError(f"Service '{service_name}' not found in bucket '{bucket}'.")
    key, salt = _read_key_salt_from_file(bucket)
    with open(secret_path, 'rb') as secret_file:
        encrypted_secret = secret_file.read()
    decrypted_secret = cry_encryption.decrypt_string(encrypted_secret, salt)
    return decrypted_secret


def update_secret(bucket, service_name, new_secret):
    """Update and re-encrypt a secret associated with a service name within a bucket."""
    secret_path = _get_secret_file_path(bucket, service_name)
    if not os.path.exists(secret_path):
        raise SecretError(f"Service '{service_name}' not found in bucket '{bucket}'.")
    key, salt = _read_key_salt_from_file(bucket)
    encrypted_secret = cry_encryption.encrypt_string(new_secret, salt)
    cry_database.update_secret(bucket, service_name, encrypted_secret)
    with open(secret_path, 'wb') as secret_file:
        secret_file.write(encrypted_secret)


def delete_secret(bucket, service_name):
    """Delete a secret and its associated file within a bucket."""
    cry_database.delete_secret(bucket, service_name)
    secret_path = _get_secret_file_path(bucket, service_name)
    if os.path.exists(secret_path):
        os.remove(secret_path)


def get_buckets():
    """Retrieve a list of all buckets available."""
    try:
        bucket_paths = [f.name for f in os.scandir(SECRETS_DIR) if f.is_dir()]
        return bucket_paths
    except FileNotFoundError:
        return []


def get_secrets(bucket):
    """Retrieve a list of all secrets stored within a specified bucket."""
    bucket_directory = os.path.join(SECRETS_DIR, bucket)
    if not os.path.exists(bucket_directory):
        return []
    secret_names = []
    for secret_file in os.listdir(bucket_directory):
        if secret_file.endswith(".json"):
            secret_name = os.path.splitext(secret_file)[0]
            secret_names.append(secret_name)
    return secret_names
