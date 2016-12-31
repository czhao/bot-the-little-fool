from functools import wraps
import flask
from flask import request, Response, current_app
import hashlib
import hmac


def authenticate():
    """Sends a 403 response indicate error"""
    return Response('signature verification failed', 403)

def requires_auth(f):

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_app.config['DEBUG'] and request.method == 'POST':
            sig = request.headers.get('x-hub-signature')
            if sig is None:
                return authenticate()
            parts = sig.split('=')
            sig_hash = parts[1]
            key = current_app.config['FB_APP_SECRET_KEY']
            hashed = hmac.new(key, request.get_data(), hashlib.sha1)
            reference = hashed.hexdigest()
            if sig_hash == reference:
                return f(*args, **kwargs)
            current_app.logger.error('verification failure %s %s',sig_hash,reference)
            return authenticate()
        else:
            # debug env
            return f(*args, **kwargs)
    return decorated