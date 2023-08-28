import base64
import os
import uuid

from globals import bucket_cache, SECRETS_DIR, SECRET_KEY_FILE
from modules import cry_database
from modules import cry_encryption
from modules import cry_utils


def bucket_exists(bucket):
    return os.path.exists(os.path.join(SECRETS_DIR, bucket))


def create_bucket(bucket):
    if not bucket_exists(bucket):
        # Generate a new key and salt for the bucket
        key = cry_encryption.generate_key()
        salt = cry_utils.generate_salt()

        # Save to Database
        client_id = str(uuid.uuid4())
        client_secret = base64.urlsafe_b64encode(os.urandom(16)).decode('utf-8')

        try:
            cry_database.backup_keys(bucket, key, client_id, client_secret)
        except Exception as e:
            print(f"Error while creating bucket: {str(e)}")
            return {'message': 'Failed to create bucket.'}, 500

        # Create Bucket Directory
        os.makedirs(os.path.join(SECRETS_DIR, bucket))

        # Store the key and salt in the key file
        with open(os.path.join(SECRETS_DIR, bucket, SECRET_KEY_FILE), 'wb') as key_file:
            key_file.write(key + salt)

        # Update the cache with the new bucket details
        bucket_cache[bucket] = {
            'client_id': client_id,
            'client_secret': client_secret
        }

        return True, client_id, base64.b64encode(client_secret.encode()).decode('utf-8')

    return {'message': 'Bucket already exists.'}, 409


def secret_exists(bucket, service_name):
    return os.path.exists(os.path.join(SECRETS_DIR, bucket, f"{service_name}.json"))


def store_secret(bucket, service_name, secret):
    secret_path = os.path.join(SECRETS_DIR, bucket, f"{service_name}.json")
    secret_master_key = os.path.join(SECRETS_DIR, bucket, SECRET_KEY_FILE)
    # Validate if the secret.key file exists
    if not os.path.exists(secret_master_key):
        raise FileNotFoundError(f"Secret key file not found for bucket '{bucket}'. Please check your configuration.")
    # Read the key and salt from the key file
    with open(secret_master_key, 'rb') as key_file:
        key_salt = key_file.read()
    key = key_salt[:32]
    salt = key_salt[32:]
    # Ensure the secret is a string (if it's bytes, convert it to a string)
    if isinstance(secret, bytes):
        secret = secret.decode()
    # Encrypt the secret
    encrypted_secret = cry_encryption.encrypt_string(key, secret.encode(), salt)
    # Save the encrypted secret to the database
    cry_database.save_secret(bucket, service_name, encrypted_secret)
    # Save the Secret to File
    with open(secret_path, 'wb') as secret_file:
        secret_file.write(encrypted_secret)


def retrieve_secret(bucket, service_name):
    secret_path = os.path.join(SECRETS_DIR, bucket, f"{service_name}.json")
    if not os.path.exists(secret_path):
        raise ValueError(f"Service '{service_name}' not found in bucket '{bucket}'.")
    secret_master_key = os.path.join(SECRETS_DIR, bucket, SECRET_KEY_FILE)
    # Validate if the secret.key file exists
    if not os.path.exists(secret_master_key):
        raise FileNotFoundError(f"Secret key file not found for bucket '{bucket}'. Please check your configuration.")
    # Read the key and salt from the key file
    with open(secret_master_key, 'rb') as key_file:
        key_salt = key_file.read()
    key = key_salt[:32]
    salt = key_salt[32:]
    # Read the encrypted secret from the file and decrypt it
    with open(secret_path, 'rb') as secret_file:
        encrypted_secret = secret_file.read()
    decrypted_secret = cry_encryption.decrypt_string(key, encrypted_secret, salt)
    return decrypted_secret.decode()


def update_secret(bucket, service_name, new_secret):
    secret_path = os.path.join(SECRETS_DIR, bucket, f"{service_name}.json")
    if not os.path.exists(secret_path):
        raise ValueError(f"Service '{service_name}' not found in bucket '{bucket}'.")
    secret_master_key = os.path.join(SECRETS_DIR, bucket, SECRET_KEY_FILE)
    # Validate if the secret.key file exists
    if not os.path.exists(secret_master_key):
        raise FileNotFoundError(f"Secret key file not found for bucket '{bucket}'. Please check your configuration.")
    # Read the key and salt from the key file
    with open(secret_master_key, 'rb') as key_file:
        key_salt = key_file.read()
    key = key_salt[:32]
    salt = key_salt[32:]
    # Encrypt the new secret
    encrypted_secret = cry_encryption.encrypt_string(key, new_secret.encode(), salt)
    # Update the encrypted secret in the database
    cry_database.update_secret(bucket, service_name, encrypted_secret)
    # Store it in the file
    with open(secret_path, 'wb') as secret_file:
        secret_file.write(encrypted_secret)


def delete_secret(bucket, service_name):
    # Delete the secret from the database
    cry_database.delete_secret(bucket, service_name)
    # Delete the secret from the File System
    bucket_path = os.path.join(SECRETS_DIR, bucket)
    secret_path = os.path.join(bucket_path, f"{service_name}.json")
    if os.path.exists(secret_path):
        os.remove(secret_path)


def get_buckets():
    try:
        bucket_paths = [f.name for f in os.scandir(SECRETS_DIR) if f.is_dir()]
        return bucket_paths
    except FileNotFoundError:
        return []


def get_secrets(bucket):
    bucket_directory = os.path.join(SECRETS_DIR, bucket)

    if not os.path.exists(bucket_directory):
        return []

    secret_names = []
    for secret_file in os.listdir(bucket_directory):
        if secret_file.endswith(".json"):
            secret_name = os.path.splitext(secret_file)[0]
            secret_names.append(secret_name)

    return secret_names
