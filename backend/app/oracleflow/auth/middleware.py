from functools import wraps
from flask import request, jsonify, g
from app.oracleflow.auth.utils import decode_token

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]

        if not token:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        payload = decode_token(token)
        if not payload:
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401

        g.user_id = payload['user_id']
        g.org_id = payload['org_id']
        g.plan = payload['plan']
        g.role = payload['role']
        return f(*args, **kwargs)
    return decorated

def require_admin(f):
    @wraps(f)
    @require_auth
    def decorated(*args, **kwargs):
        if g.role != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated
