import os
from functools import wraps
from flask import request, jsonify
from jose import JWTError, jwt
from datetime import datetime, timedelta
from models import User
from werkzeug.security import generate_password_hash, check_password_hash

JWT_SECRET = os.environ.get('JWT_SECRET', 'change_this_secret')
JWT_ALGO = 'HS256'
JWT_EXP_MIN = int(os.environ.get('JWT_EXP_MIN', 60*24))

def create_token(identity: dict):
    payload = identity.copy()
    payload['exp'] = datetime.utcnow() + timedelta(minutes=JWT_EXP_MIN)
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)
    return token

def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload
    except JWTError:
        return None

def jwt_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth = request.headers.get('Authorization', None)
            if not auth:
                return jsonify({'msg': 'Missing Authorization header'}), 401
            parts = auth.split()
            if parts[0].lower() != 'bearer' or len(parts) != 2:
                return jsonify({'msg': 'Invalid Authorization header'}), 401
            token = parts[1]
            data = verify_token(token)
            if not data:
                return jsonify({'msg': 'Invalid or expired token'}), 401
            if role:
                if isinstance(role, (list,tuple)):
                    if data.get('role') not in role:
                        return jsonify({'msg': 'Insufficient role'}), 403
                else:
                    if data.get('role') != role:
                        return jsonify({'msg': 'Insufficient role'}), 403
            request.user = data
            return f(*args, **kwargs)
        return wrapper
    return decorator

def create_user(db, username: str, password: str, role: str='viewer'):
    h = generate_password_hash(password)
    user = User(username=username, password_hash=h, role=role)
    db.add(user)
    db.commit()
    return user

def authenticate_user(db, username: str, password: str):
    user = db.query(User).filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return None
    return {'id': user.id, 'username': user.username, 'role': user.role}
