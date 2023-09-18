# Global variable to store bucket details in memory
import os

from flask_restx import reqparse

import logging

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
