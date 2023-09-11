# secrets-manager

1. Web Templates:
These are HTML, CSS, and JavaScript files for rendering the web interface.

./templates/home.html: The main homepage template for the service.
./templates/static/bootstrap.min.css: Bootstrap CSS framework.
./templates/static/favicon.ico: Website favicon.
./templates/static/jquery.min.js: jQuery library.
./templates/static/bootstrap.min.js: Bootstrap JavaScript library.

2. Configuration:
Files associated with various configurations required for the service.

./config/nginx.conf: Configuration for the Nginx web server.
./config/database_config.json: Configuration for the database.
./config/crystal/dummy.json: Configuration example.
./config/crystal/platform.json: Configuration for "platform" bucket.
./config/crystal/database.json: Configuration for "database" bucket.

3. Modules:
Core functionality and utilities.

./modules/cry_encryption.py: Encryption and decryption functions.
./modules/cry_initialize.py: Initialization processes, e.g., setting up the database.
./modules/cry_gen_docs.py: Module for documentation generation.
./modules/cry_secrets_management.py: Core secrets management functions.
./modules/cry_email_sender.py: Module for sending emails.
./modules/cry_auth.py: Authorization and authentication functions.
./modules/cry_utils.py: Various utility functions.
./modules/cry_database.py: Database interactions and related functions.

4. Routes:
End-points for the API and their associated functions.

./routes/cry_home.py: Renders the homepage.
./routes/cry_create_secret.py: Endpoint to create a new secret.
./routes/cry_decrypt_str.py: Endpoint for decryption.
./routes/cry_delete_secret.py: Endpoint to delete a secret.
./routes/cry_get_secrets_list.py: Fetches a list of all secrets.
./routes/cry_encrypt_str.py: Endpoint for encryption.
./routes/cry_create_bucket.py: Endpoint to create a bucket.
./routes/cry_authorize.py: Authorization endpoint.
./routes/cry_generate_secret.py: Generates a secret.
./routes/cry_get_buckets.py: Fetches a list of all buckets.
./routes/cry_generate_password.py: Generates a password.
./routes/cry_update_secret.py: Endpoint to update a secret.
./routes/cry_get_secret.py: Fetches details of a specific secret.
./routes/init.py: Route initialization.

5. Main Application:
./main/cry_secrets_manager.py: Main application entry point.

6. Miscellaneous:
./Dockerfile: Defines the Docker container for this application.
./globals.py: Contains global constants.
./sql/create_table.sql: SQL script to create the required tables.
./requirements.txt: Lists all Python dependencies.
