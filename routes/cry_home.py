from flask import render_template, make_response
from flask_restx import Resource, Namespace
import logging
from globals import LOG_LEVEL
from modules import cry_secrets_management

logging.basicConfig(level=LOG_LEVEL)

ns = Namespace('home', description='Home Route Namespace')


@ns.route('/', doc=False)  # Exclude from Swagger UI
class Home(Resource):
    """
    Resource to serve the home page. This displays a list of buckets and their corresponding secrets.
    """

    @staticmethod
    def get():
        try:
            buckets = cry_secrets_management.get_buckets()
            secrets_list = {}
            for bucket in buckets:
                secrets_files = cry_secrets_management.get_secrets(bucket)
                secrets_list[bucket] = secrets_files

            # Render the template
            html_content = render_template('home.html', buckets=buckets, secrets=secrets_list)

            # Create a response with the correct Content-Type header
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html'
            logging.info("Successfully rendered home page with list of buckets and secrets.")
            return response

        except Exception as e:
            logging.error(f"Error encountered while rendering home page: {str(e)}")
            return {'error': 'Internal server error'}, 500
