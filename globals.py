# Global variable to store bucket details in memory
import logging
import os

from flask_restx import reqparse
from keycloak import KeycloakOpenID

# Define the global logging level
LOG_LEVEL = logging.DEBUG

# Global cache
bucket_cache = {}

# Environment
server_env = os.environ.get('SERVERENV', "DEV")

# Global Variables
SECRETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '', 'secrets')
SECRET_KEY_FILE = "secret.key"
BUCKET_KEYS = {}  # Store the encryption keys for each bucket
BUCKETS = {}  # Store the list of keys for each bucket

# Database Config Files
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', server_env, 'database_config.json')
SQL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '', 'sql', 'create_table.sql')

# Define the RequestParser for handling authentication
auth_parser = reqparse.RequestParser()
auth_parser.add_argument('Authorization', location='headers', required=True, help='Bearer <token>')

web_port = '7446'

# KeyCloak Configuration
server_url = 'https://crystal-' + server_env.lower() + '.systems.uk.hsbc:4443/auth/'
client_secret_key = 'None'
realm_name = 'CRYSTAL'
client_id = 'cry' + server_env.lower()

# Initialize Keycloak client
keycloak_openid = KeycloakOpenID(
    server_url=server_url,
    client_id=client_id,
    realm_name=realm_name,
    client_secret_key=client_secret_key
)

# Global KEY
# Fetch SECRET_KEY from environment variable CRY_INFO
SECRET_KEY = os.environ.get("CRY_INFO", "UGFwcHVDYW50RGFuY2VTYWFsYUAyMDIwMzEjJCUK")