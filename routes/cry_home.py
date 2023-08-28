from flask import render_template, make_response
from flask_restx import Resource, Namespace
from modules import cry_secrets_management

ns = Namespace('home', description='Home Route Namespace')


@ns.route('/', doc=False)  # Add doc=False here to exclude from Swagger
class Home(Resource):
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

            return response
        except Exception as e:
            return {'error': str(e)}, 500
