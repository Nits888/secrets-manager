from flask import render_template, make_response
from flask_restx import Resource, Namespace
import logging
from globals import LOG_LEVEL
from modules import cry_secrets_management

logging.basicConfig(level=LOG_LEVEL)

ns = Namespace('crystal-secrets-manager', description='Home Route Namespace')


@ns.route('/', doc=False)  # Exclude from Swagger UI
class Home(Resource):
    """
    Resource to serve the home page. This displays a list of buckets and their corresponding secrets.
    """

    @staticmethod
    def get():
        try:
            bucket_pairs = cry_secrets_management.get_buckets()  # Rename to be more clear
            secrets_list = {}
            for app_name, bucket_name in bucket_pairs:
                secrets_files = cry_secrets_management.get_secrets(bucket_name, app_name)
                if app_name not in secrets_list:
                    secrets_list[app_name] = {}

                secrets_list[app_name][bucket_name] = secrets_files

            version = 'cry-sec-V1.0.0'
            # Render the template
            html_content = render_template('home.html', buckets=bucket_pairs, secrets=secrets_list, version=version)

            # Create a response with the correct Content-Type header
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html'
            logging.info("Successfully rendered home page with list of buckets and secrets.")
            return response

        except Exception as e:
            logging.error(f"Error encountered while rendering home page: {str(e)}")
            return {'error': 'Internal server error'}, 500
