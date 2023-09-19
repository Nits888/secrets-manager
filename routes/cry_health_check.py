"""
cry_health_check.py
-------------------

Module for checking the health status of the Secrets Management Service.
"""

from flask_restx import Namespace, Resource
from http import HTTPStatus

ns = Namespace('health', description='Health check for Secrets Management Service')


@ns.route('/')
class HealthResource(Resource):

    @ns.doc(
        responses={
            HTTPStatus.OK: 'Service is healthy.',
            HTTPStatus.SERVICE_UNAVAILABLE: 'Service is unavailable.'
        })
    def get(self):
        """
        Check the health of the service.
        Returns a simple JSON object indicating the service is up.
        """
        try:
            return {'status': 'healthy'}, HTTPStatus.OK
        except Exception as e:
            return {'status': 'unhealthy', 'reason': str(e)}, HTTPStatus.SERVICE_UNAVAILABLE
