import json
import os

import psycopg2
from psycopg2 import pool

from globals import CONFIG_FILE, SQL_FILE, SECRETS_DIR

from modules import cry_encryption

# Define BACKUP_POOL
BACKUP_POOL = None


def load_config():
    with open(CONFIG_FILE) as file:
        return json.load(file)


def load_sql_script():
    with open(SQL_FILE) as file:
        return file.read()


def create_connection_pool():
    global BACKUP_POOL
    if not BACKUP_POOL:
        config = load_config()
        ddl_password_info = cry_encryption.decrypt_text(config["DDL_PASSWORD"]["value"], config["DDL_PASSWORD"]["salt"])
        ddl_password = ddl_password_info.get("decrypted_text")
        BACKUP_POOL = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            host=config["DB_HOST"],
            port=config["DB_PORT"],
            database=config["DB_NAME"],
            user=config["DDL_USER"],
            password=ddl_password
        )


def backup_keys(bucket, key, client_id, client_secret):
    # create_connection_pool()
    connection = BACKUP_POOL.getconn()
    cursor = connection.cursor()
    query = "INSERT INTO bucket_keys (bucket_name, encryption_key, client_id, client_secret) VALUES (%s, %s, %s, %s);"
    cursor.execute(query, (bucket, key, client_id, client_secret))
    connection.commit()
    cursor.close()
    BACKUP_POOL.putconn(connection)


def create_table():
    try:
        # Get a connection using DML credentials for table creation
        config = load_config()
        dml_password_info = cry_encryption.decrypt_text(config["DML_PASSWORD"]["value"], config["DML_PASSWORD"]["salt"])
        dml_password = dml_password_info.get("decrypted_text")
        ddl_conn = psycopg2.connect(
            host=config["DB_HOST"],
            port=config["DB_PORT"],
            database=config["DB_NAME"],
            user=config["DML_USER"],
            password=dml_password
        )
        # Open a cursor to perform database operations
        ddl_cur = ddl_conn.cursor()
        # Read the SQL queries from create_table.sql file
        with open("sql/create_table.sql", "r") as create_table_file:
            create_table_queries = create_table_file.read()
        # Execute the queries to create the tables
        ddl_cur.execute(create_table_queries)
        # Commit the transaction and close the cursor
        ddl_conn.commit()
        ddl_cur.close()
        # Close the connection with DDL credentials
        ddl_conn.close()

    except Exception as e:
        print(f"An error occurred while creating the tables: {e}")


def initialize_buckets_and_keys_from_db():
    try:
        # Create a connection pool for backup_keys
        create_connection_pool()
        # Get bucket names and keys from the database and store in combined list
        connection = BACKUP_POOL.getconn()
        cursor = connection.cursor()
        # Execute the SELECT query to fetch bucket names and keys
        query = "SELECT bucket_name, encryption_key FROM bucket_keys;"
        cursor.execute(query)
        # Fetch the combined list of bucket names and keys
        bucket_keys_list = cursor.fetchall()
        cursor.close()
        BACKUP_POOL.putconn(connection)
        return bucket_keys_list
    except Exception as e:
        print(f"An error occurred while retrieving all Buckets: {e}")


def save_secret(bucket_name, secret_name, encrypted_secret):
    try:
        # Get a connection from the connection pool with DML permissions
        conn = BACKUP_POOL.getconn()
        # Open a cursor to perform database operations
        cur = conn.cursor()
        # Prepare the query to insert or update the encrypted_secret into the secrets table
        query = "INSERT INTO secrets (bucket_name, secret_name, encrypted_secret) VALUES (%s, %s, %s) " \
                "ON CONFLICT (bucket_name, secret_name) DO UPDATE SET encrypted_secret = EXCLUDED.encrypted_secret;"
        # Execute the query to insert or update the encrypted_secret
        cur.execute(query, (bucket_name, secret_name, psycopg2.Binary(encrypted_secret)))
        # Commit the changes to the database
        conn.commit()
        # Close the cursor and return the connection to the pool
        cur.close()
        BACKUP_POOL.putconn(conn)
    except Exception as e:
        print(f"An error occurred while saving the secret: {e}")


def update_secret(bucket_name, secret_name, encrypted_secret):
    try:
        # Get a connection from the connection pool with DML permissions
        conn = BACKUP_POOL.getconn()
        # Open a cursor to perform database operations
        cur = conn.cursor()
        # Prepare the query to update the encrypted_secret in the secrets table
        query = "UPDATE secrets SET encrypted_secret = %s WHERE bucket_name = %s AND secret_name = %s;"
        # Execute the query to update the encrypted_secret
        cur.execute(query, (psycopg2.Binary(encrypted_secret), bucket_name, secret_name))
        # Commit the changes to the database
        conn.commit()
        # Close the cursor and return the connection to the pool
        cur.close()
        BACKUP_POOL.putconn(conn)
    except Exception as e:
        print(f"An error occurred while updating the secret: {e}")


def delete_secret(bucket_name, secret_name):
    try:
        # Get a connection from the connection pool with DML permissions
        conn = BACKUP_POOL.getconn()
        # Open a cursor to perform database operations
        cur = conn.cursor()
        # Prepare the query to delete the secret from the secrets table
        query = "DELETE FROM secrets WHERE bucket_name = %s AND secret_name = %s;"
        # Execute the query to delete the secret
        cur.execute(query, (bucket_name, secret_name))
        # Commit the changes to the database
        conn.commit()
        # Close the cursor and return the connection to the pool
        cur.close()
        BACKUP_POOL.putconn(conn)
    except Exception as e:
        print(f"An error occurred while deleting the secret: {e}")


def get_all_secrets(batch_size=1000):
    try:
        # Get a connection from the connection pool with DML permissions
        conn = BACKUP_POOL.getconn()
        # Open a cursor to perform database operations
        cur = conn.cursor()
        # Prepare the query to retrieve all secrets from the secrets table
        query = "SELECT bucket_name, secret_name, encrypted_secret FROM secrets;"
        # Execute the query to retrieve secrets in batches
        cur.execute(query)
        # Fetch the first batch of rows
        batch = cur.fetchmany(batch_size)
        # Initialize the result list
        secrets = []
        # Fetch secrets in batches until all rows are retrieved
        while batch:
            secrets.extend(batch)
            batch = cur.fetchmany(batch_size)
        # Close the cursor and return the connection to the pool
        cur.close()
        BACKUP_POOL.putconn(conn)
        return secrets
    except Exception as e:
        print(f"An error occurred while retrieving all secrets: {e}")


def sync_keys():
    # Get a connection from the connection pool with DML permissions
    conn = BACKUP_POOL.getconn()
    # Open a cursor to perform database operations
    cur = conn.cursor()
    query = "SELECT bucket_name, encryption_key FROM bucket_keys;"
    keys = cur(query, fetch=True)
    for key in keys:
        bucket_name, encryption_key = key
        bucket_directory = os.path.join(SECRETS_DIR, bucket_name)
        if not os.path.exists(bucket_directory):
            os.makedirs(bucket_directory)
        key_file_path = os.path.join(bucket_directory, "secret.key")
        with open(key_file_path, "wb") as key_file:
            key_file.write(encryption_key)


def get_all_buckets():
    # create_connection_pool()
    connection = BACKUP_POOL.getconn()
    cursor = connection.cursor()
    query = "SELECT bucket_name, encryption_key, client_id, client_secret FROM bucket_keys;"
    cursor.execute(query)
    result = cursor.fetchall()
    connection.commit()
    cursor.close()
    BACKUP_POOL.putconn(connection)
    return result
