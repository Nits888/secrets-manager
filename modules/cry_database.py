import json
import logging
import os
import psycopg2
from psycopg2 import pool
from globals import CONFIG_FILE, SQL_FILE, LOG_LEVEL, SECRETS_DIR

# Set up logging
logging.basicConfig(level=LOG_LEVEL)

# Create the DML connection pool at startup
BACKUP_POOL = None


def load_config():
    """Load the configuration settings from the specified CONFIG_FILE.

    Returns:
        dict: A dictionary containing configuration settings.
    """
    with open(CONFIG_FILE) as file:
        logging.info("Loading Database Configuration File")
        return json.load(file)


def load_sql_script():
    """Load the SQL script from the specified SQL_FILE.

    Returns:
        str: SQL script as a string.
    """
    with open(SQL_FILE) as file:
        logging.info("Loading SQL Configuration File")
        return file.read()


def create_dml_connection_pool():
    """Create a connection pool for DML operations using the loaded configuration settings.

    The function initializes the global variable BACKUP_POOL with the connection pool.
    """
    global BACKUP_POOL
    if not BACKUP_POOL:
        logging.info("Creating Connection POOL")
        config = load_config()
        dml_info = os.environ.get('DMLINFO')
        BACKUP_POOL = pool.SimpleConnectionPool(
            minconn=2,
            maxconn=8,
            host=config["DB_HOST"],
            port=config["DB_PORT"],
            database=config["DB_NAME"],
            user=config["DML_USER"],
            password=dml_info
        )


create_dml_connection_pool()  # Initialize the pool at startup


def backup_keys(bucket, combined_key_salt, client_id, app_name):
    """Backup encryption keys and related data into the database.

    Args:
        bucket (str): Bucket name.
        combined_key_salt (str): Combined encryption key and salt.
        client_id (str): Client ID.
        app_name (str) : Application Name

    Raises:
        Exception: If any issue occurs during the backup process.
    """
    try:
        with BACKUP_POOL.getconn() as conn, conn.cursor() as cur:
            query = ("INSERT INTO bucket_keys (app_name, bucket_name, encryption_key_salt, client_id) "
                     "VALUES (%s, %s, %s, %s);")
            cur.execute(query, (app_name, bucket, combined_key_salt, client_id))
            conn.commit()
    except Exception as e:
        logging.error(f"Error backing up keys: {e}")
        conn.rollback()  # Rollback will be effective as conn is still in context
        raise  # Re-raise the exception after handling it.


def create_table():
    """Creates necessary tables using the SQL script from the SQL_FILE.

    Uses the DDL connection information from the configuration settings.
    """
    config = load_config()
    ddl_info = os.environ.get('DDLINFO')
    try:
        logging.info(f"Attempting to Check and Create Table(s) from SQL - If Missing")
        with psycopg2.connect(
                host=config["DB_HOST"],
                port=config["DB_PORT"],
                database=config["DB_NAME"],
                user=config["DDL_USER"],
                password=ddl_info
        ) as conn, conn.cursor() as cur:
            with open(SQL_FILE, "r") as create_table_file:
                create_table_queries = create_table_file.read()
            cur.execute(create_table_queries)
    except Exception as e:
        logging.error(f"Error creating tables: {e}")


def sync_keys():
    """Sync encryption keys from the database to the local file system.

    Each bucket's key is saved as a separate file in its respective directory.
    """
    try:
        with BACKUP_POOL.getconn() as conn, conn.cursor() as cur:
            query = "SELECT app_name, bucket_name, encryption_key_salt FROM bucket_keys;"
            cur.execute(query)
            keys = cur.fetchall()

            for key in keys:
                app_name, bucket_name, encryption_key_salt = key
                bucket_directory = os.path.join(SECRETS_DIR, app_name, bucket_name)
                if not os.path.exists(bucket_directory):
                    os.makedirs(bucket_directory)
                key_file_path = os.path.join(bucket_directory, "secret.key")
                with open(key_file_path, "wb") as key_file:
                    key_file.write(encryption_key_salt)
    except Exception as e:
        logging.error(f"An error occurred while syncing keys: {e}")


def initialize_buckets_and_keys_from_db():
    """Retrieve bucket names and keys from the database.

    Returns:
        list: A list of tuples containing bucket names and their corresponding encryption keys.
    """
    try:
        # Get a connection from the connection pool
        with BACKUP_POOL.getconn() as connection:
            # Use a cursor to execute the query and fetch results
            with connection.cursor() as cursor:
                # Execute the SELECT query to fetch bucket names and keys
                query = "SELECT app_name, bucket_name, encryption_key_salt FROM bucket_keys;"
                cursor.execute(query)

                # Fetch the combined list of bucket names and keys
                bucket_keys_list = cursor.fetchall()

        # Return the connection to the pool is automatically handled by the context manager
        return bucket_keys_list

    except Exception as e:
        logging.error(f"An error occurred while retrieving all Buckets: {e}")
        return []  # Return an empty list in case of any error


def save_secret(bucket_name, secret_name, encrypted_secret, app_name):
    """Save or update a secret in the database.

    Args:
        bucket_name (str): The name of the bucket.
        secret_name (str): The name of the secret.
        encrypted_secret (bytes): The encrypted secret data.
        app_name (str): Application Name

    Raises:
        Exception: If an error occurs during database operations.
    """
    try:
        # Get a connection from the connection pool with DML permissions
        with BACKUP_POOL.getconn() as conn:
            # Use a cursor to perform database operations
            with conn.cursor() as cur:
                # Prepare the query to insert or update the encrypted_secret into the secrets table
                query = """
                    INSERT INTO secrets (app_name, bucket_name, secret_name, encrypted_secret) 
                    VALUES (%s, %s, %s, %s) 
                    ON CONFLICT (app_name, bucket_name, secret_name) 
                    DO UPDATE SET encrypted_secret = EXCLUDED.encrypted_secret;
                """
                # Execute the query to insert or update the encrypted_secret
                cur.execute(query, (app_name, bucket_name, secret_name, psycopg2.Binary(encrypted_secret)))
                # Commit the changes to the database
                conn.commit()

        # The returning of the connection to the pool is automatically handled by the context manager

    except Exception as e:
        logging.error(
            f"An error occurred while saving the secret for bucket '{bucket_name}' and secret '{secret_name}': {e}")
        raise e  # Re-raise the exception to allow potential handling by the caller


def update_secret(bucket_name, secret_name, encrypted_secret, app_name):
    """Update a secret in the database.

    Args:
        bucket_name (str): The name of the bucket.
        secret_name (str): The name of the secret.
        encrypted_secret (bytes): The updated encrypted secret data.
        app_name (str): Application Name

    Raises:
        Exception: If an error occurs during database operations.
    """
    try:
        with BACKUP_POOL.getconn() as conn:
            with conn.cursor() as cur:
                query = """
                    UPDATE secrets 
                    SET encrypted_secret = %s 
                    WHERE app_name = %s AND bucket_name = %s AND secret_name = %s;
                """
                cur.execute(query, (psycopg2.Binary(encrypted_secret), app_name, bucket_name, secret_name))
                conn.commit()

    except Exception as e:
        logging.error(f"An error occurred while updating the secret for bucket "
                      f"'{bucket_name}' and secret '{secret_name}': {e}")
        raise e


def delete_secret(bucket_name, secret_name, app_name):
    """Delete a secret from the database.

    Args:
        bucket_name (str): The name of the bucket.
        secret_name (str): The name of the secret.
        app_name(str) : The Application name of the Bucket.

    Raises:
        Exception: If an error occurs during database operations.
    """
    try:
        with BACKUP_POOL.getconn() as conn:
            with conn.cursor() as cur:
                query = """
                    DELETE FROM secrets 
                    WHERE app_name = %s AND bucket_name = %s AND secret_name = %s;
                """
                cur.execute(query, (app_name, bucket_name, secret_name))
                conn.commit()

    except Exception as e:
        logging.error(f"An error occurred while deleting the secret for bucket "
                      f"'{bucket_name}' and secret '{secret_name}': {e}")
        raise e


def get_all_secrets(batch_size=1000):
    """Retrieve all secrets from the database in batches.

    Args:
        batch_size (int): The number of records to fetch in each batch.

    Returns:
        list: List of all secrets.

    Raises:
        Exception: If an error occurs during database operations.
    """
    secrets = []
    try:
        with BACKUP_POOL.getconn() as conn:
            with conn.cursor() as cur:
                query = "SELECT app_name, bucket_name, secret_name, encrypted_secret FROM secrets;"
                cur.execute(query)

                batch = cur.fetchmany(batch_size)
                while batch:
                    secrets.extend(batch)
                    batch = cur.fetchmany(batch_size)

    except Exception as e:
        logging.error(f"An error occurred while retrieving all secrets: {e}")
        raise e

    return secrets


def get_all_buckets():
    """Retrieve all bucket details from the database.

    Returns:
        list: List of all buckets' details.

    Raises:
        Exception: If an error occurs during database operations.
    """
    try:
        with BACKUP_POOL.getconn() as conn:
            with conn.cursor() as cur:
                query = "SELECT app_name, bucket_name, encryption_key_salt, client_id FROM bucket_keys;"
                cur.execute(query)
                result = cur.fetchall()

    except Exception as e:
        logging.error(f"An error occurred while retrieving all buckets: {e}")
        raise e

    return result
