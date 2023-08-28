from flask import request
from flask_httpauth import HTTPTokenAuth

from globals import bucket_cache

auth = HTTPTokenAuth(scheme='Bearer')


@auth.verify_token
def verify_token(token):
    # Get the bucket_name from the request data
    bucket_name = request.json.get('bucket_name', None)

    # Fetch the client_id and client_secret associated with the bucket_name from the cache
    credentials = bucket_cache.get(bucket_name, None)
    if credentials:
        client_id, client_secret = credentials['client_id'], credentials['client_secret']
    else:
        client_id, client_secret = None, None

    # Validate the token using the client_id and client_secret
    if token and token == f"{client_id}:{client_secret}":
        return True

    return False
