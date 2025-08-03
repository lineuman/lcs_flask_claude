import bcrypt
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, get_jwt
from app.models import User

jwt = JWTManager()

# 黑名单存储（用于注销功能）
blacklisted_tokens = set()

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    return jwt_payload['jti'] in blacklisted_tokens

def authenticate_user(username, password):
    user = User.query.filter_by(username=username).first()
    if user and bcrypt.checkpw(password.encode('utf-8'), user.password):
        return user
    return None

def create_user(username, password, role='user'):
    if User.query.filter_by(username=username).first():
        return None
    
    new_user = User(
        username=username,
        password=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()),
        role=role
    )
    return new_user

def get_current_user():
    current_user = get_jwt_identity()
    if current_user:
        return User.query.filter_by(username=current_user).first()
    return None

def logout_user(jti):
    blacklisted_tokens.add(jti)
    return True