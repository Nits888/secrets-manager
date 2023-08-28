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

from modules import cry_database
from modules import cry_gen_docs
from modules import cry_initialize

import routes.cry_home

app = Flask(__name__, template_folder='../templates')
api = Api(app, doc='/swagger/', title='AmethystKey - Secret Management API', description='API endpoints for secret '
                                                                                         'management')

# Create a Namespace
ns = Namespace('secrets', description='CRYSTAL Platform Secret Management Service')


# Custom JSON encoder for converting bytes to base64
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        try:
            if isinstance(o, bytes):
                return base64.urlsafe_b64encode(o).decode()
            return super().default(o)
        except TypeError:
            return str(o)


app.json_encoder = CustomJSONEncoder

# Create a logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Get the absolute path to the routes folder
routes_folder = 'routes'
route_files = [filename for filename in os.listdir(routes_folder) if filename.startswith('cry_')]

# Dynamically import and add namespaces from route files
for route_file in route_files:
    if route_file != 'cry_home.py':  # Exclude the specific route file
        module_name = f'routes.{os.path.splitext(route_file)[0]}'
        module = importlib.import_module(module_name)
        api.add_namespace(module.ns)

# Add the cry_home namespace for the root route
api.add_namespace(routes.cry_home.ns)


# Define a custom ordering function for the endpoints
def custom_order(namespace, func):
    return api.namespaces.index(namespace), namespace.resources.index(func)


# Set the custom ordering function for the API
api._default_order = custom_order


# Doc Route for App
@app.route('/docs/')
def render_docs():
    docs_dir = os.path.join(os.path.dirname(__file__), '../docs/_build')
    return send_from_directory(docs_dir, 'index.html')


# Route to serve static files
@app.route('/docs/<path:filename>')
def serve_static(filename):
    return send_from_directory('../docs/_build', filename)


# Initialization
logging.info("Generating Documentation")
cry_gen_docs.generate_documentation()
logging.info("Initializing Secrets Manager Service")
cry_initialize.initialize_app()


# Start the synchronization loop in a separate thread
def start_sync_thread():
    while True:
        logging.info("Syncing Buckets & Keys from Database")
        bucket_keys_list = cry_database.initialize_buckets_and_keys_from_db()
        cry_initialize.initialize_buckets(bucket_keys_list)
        logging.info("Syncing Secrets from Database")
        cry_initialize.initialize_secrets_from_db()
        # time.sleep(3600)  # 1 hour in seconds
        time.sleep(600)  # 5 minute in seconds


if __name__ == '__main__':
    # Create the thread for synchronization
    sync_thread = threading.Thread(target=start_sync_thread)
    sync_thread.start()

    # Start Waitress server with HTTPS
    serve(
        app,
        host='127.0.0.1',
        port=7443,  # This should match the proxy_pass address in Nginx
        threads=8
    )
