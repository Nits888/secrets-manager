# Global variable to store bucket details in memory
import os

from flask_restx import reqparse

bucket_cache = {}

# Global Variables
SECRETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '', 'secrets')
SECRET_KEY_FILE = "secret.key"
BUCKET_KEYS = {}  # Store the encryption keys for each bucket
BUCKETS = {}  # Store the list of keys for each bucket

# Database Config Files
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '', 'config', 'database_config.json')
SQL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '', 'sql', 'create_table.sql')

# Define the RequestParser for handling authentication
auth_parser = reqparse.RequestParser()
auth_parser.add_argument('Authorization', location='headers', required=True, help='Bearer <token>')