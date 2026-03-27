import bcrypt
import jwt
import os
from datetime import datetime, timezone, timedelta

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    import warnings
    warnings.warn("SECRET_KEY not set! Using insecure default. Set SECRET_KEY env var in production.", stacklevel=2)
    SECRET_KEY = 'oracleflow-dev-only-insecure-key-' + os.urandom(8).hex()

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, password_hash):
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def create_token(user_id, org_id, plan, role, expires_hours=24):
    payload = {
        'user_id': user_id,
        'org_id': org_id,
        'plan': plan,
        'role': role,
        'exp': datetime.now(timezone.utc) + timedelta(hours=expires_hours),
        'iat': datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def decode_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
