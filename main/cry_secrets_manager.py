import base64
import importlib
import json
import logging
import os
import threading
import time

from flask import Flask, send_from_directory
from flask_restx import Api, Namespace
from waitress import serve

import routes.cry_home
from modules import cry_database
from modules import cry_gen_docs
from modules import cry_initialize

from globals import LOG_LEVEL

# Flask app initialization
app = Flask(__name__, template_folder='../templates', static_folder='../templates/static')
api = Api(app, doc='/swagger/', title='AmethystKey - Secret Management API',
          description='API endpoints for secret management')

# Namespace initialization
ns = Namespace('secrets', description='CRYSTAL Platform Secret Management Service')


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle bytes and encode them to base64."""

    def default(self, o):
        try:
            if isinstance(o, bytes):
                return base64.urlsafe_b64encode(o).decode()
            return super().default(o)
        except TypeError:
            return str(o)


app.json_encoder = CustomJSONEncoder

# Logging setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=LOG_LEVEL)

# Dynamically loading route files
routes_folder = 'routes'
route_files = [filename for filename in os.listdir(routes_folder) if filename.startswith('cry_')]
for route_file in route_files:
    if route_file != 'cry_home.py':
        module_name = f'routes.{os.path.splitext(route_file)[0]}'
        module = importlib.import_module(module_name)
        api.add_namespace(module.ns)

api.add_namespace(routes.cry_home.ns)


def custom_order(namespace, func):
    """Ordering function for arranging API endpoints."""

    return api.namespaces.index(namespace), namespace.resources.index(func)


api._default_order = custom_order


@app.route('/docs/')
def render_docs():
    """Endpoint to serve the main documentation page."""

    docs_dir = os.path.join(os.path.dirname(__file__), '../docs/_build')
    return send_from_directory(docs_dir, 'index.html')


@app.route('/docs/<path:filename>')
def serve_static(filename):
    """Endpoint to serve static files from the documentation folder."""

    return send_from_directory('../docs/_build', filename)


# Initialization procedures
logging.info("Generating Documentation")
cry_gen_docs.generate_documentation()
logging.info("Initializing Secrets Manager Service")
cry_initialize.initialize_app()

bucket_keys_lock = threading.Lock()


def start_sync_thread():
    """Start a synchronization loop to periodically sync buckets, keys, and secrets from the database."""

    while True:
        logging.info("Syncing Buckets & Keys from Database")
        with bucket_keys_lock:
            bucket_keys_list = cry_database.initialize_buckets_and_keys_from_db()
            cry_initialize.initialize_buckets(bucket_keys_list)
        logging.info("Syncing Secrets from Database")
        cry_initialize.initialize_secrets_from_db()
        time.sleep(600)  # Sync every 10 minutes


if __name__ == '__main__':
    # Initialize synchronization thread
    sync_thread = threading.Thread(target=start_sync_thread)
    sync_thread.start()

    # Start the server
    serve(
        app,
        host='127.0.0.1',
        port=7443,
        threads=8
    )
