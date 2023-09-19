import base64
import importlib
import json
import logging
import os
import threading
import time

from flask import Flask, send_from_directory, request
from flask_restx import Api, Namespace
from waitress import serve
from flask_limiter.util import get_remote_address
from flask_limiter import Limiter

import routes.cry_home
from modules import cry_database
from modules import cry_gen_docs
from modules import cry_initialize

from globals import LOG_LEVEL

# Flask app initialization
app = Flask(__name__, template_folder='../templates', static_folder='../templates/static')
# api = Api(app, doc='/swagger/', title='AmethystKey - Secret Management API',
#          description='API endpoints for secret management')
api = Api(app, doc='/api/docs/', title='AmethystKey - Secret Management API',
          description='API endpoints for secret management')

# Flask App Secret Key - Dynamic
app.config['SECRET_KEY'] = os.urandom(32).hex()

# Rate Limiter setup
limiter = Limiter(
    key_func=get_remote_address
)

limiter.init_app(app)


@limiter.request_filter
def exempt_users():
    return False  # No exemption, apply the limiter to everyone


@limiter.limit("5 per minute")
@app.route("/<path:path>")
def catch_all(path):
    return app.send_static_file(path)


@app.after_request
def apply_security_headers(response):
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


@app.before_request
def log_real_ip():
    x_real_ip = request.headers.get('X-Real-IP')
    if x_real_ip:
        logging.info(f"Incoming Request from IP {x_real_ip} on Route: {request.endpoint}")
    else:
        logging.info(f"Incoming Request from Unknown IP on Route: {request.endpoint}")


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
route_files.sort()  # Sort the list of route files alphabetically

# Add the home route first
api.add_namespace(routes.cry_home.ns)

# Add other route files
for route_file in route_files:
    if route_file != 'cry_home.py':
        module_name = f'routes.{os.path.splitext(route_file)[0]}'
        module = importlib.import_module(module_name)
        api.add_namespace(module.ns)


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
    # serve(
    #    app,
    #    host='127.0.0.1',
    #    port=7443,
    #    threads=8,
    #    _quiet=False
    # )
    print(app.url_map)
    app.run()
