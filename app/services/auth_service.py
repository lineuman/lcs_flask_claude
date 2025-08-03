import bcrypt
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, get_jwt, decode_token
from app.services.user_service import UserService
from typing import Optional, Dict, Any

jwt = JWTManager()

# 黑名单存储（用于注销功能）
blacklisted_tokens = set()

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    """检查token是否被撤销"""
    return jwt_payload['jti'] in blacklisted_tokens

class AuthService:
    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        用户认证
        
        Args:
            username: 用户名
            password: 密码
        
        Returns:
            认证结果字典(包含access_token和用户信息)或None
        """
        user = UserService.get_user_by_username(username)
        if user and UserService.verify_password(user, password):
            access_token = create_access_token(identity=username)
            return {
                'access_token': access_token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'role': user.role,
                    'email': user.email,
                    'full_name': user.full_name
                }
            }
        return None
    
    @staticmethod
    def register_user(username: str, password: str, role: str = 'user', **kwargs) -> Optional[Dict[str, Any]]:
        """
        用户注册
        
        Args:
            username: 用户名
            password: 密码
            role: 用户角色
            **kwargs: 其他用户信息
        
        Returns:
            注册结果或None(如果用户名已存在)
        """
        if UserService.get_user_by_username(username):
            return None
        
        new_user = UserService.create_user(username, password, role, **kwargs)
        if new_user:
            from app.models import db
            db.session.commit()
            
            access_token = create_access_token(identity=username)
            return {
                'access_token': access_token,
                'user': {
                    'id': new_user.id,
                    'username': new_user.username,
                    'role': new_user.role,
                    'email': new_user.email,
                    'full_name': new_user.full_name
                }
            }
        return None
    
    @staticmethod
    def get_current_user() -> Optional[Any]:
        """获取当前登录用户"""
        current_user = get_jwt_identity()
        if current_user:
            return UserService.get_user_by_username(current_user)
        return None
    
    @staticmethod
    def get_current_user_id() -> Optional[int]:
        """获取当前登录用户的ID"""
        current_user = AuthService.get_current_user()
        return current_user.id if current_user else None
    
    @staticmethod
    def logout_user(jti: str) -> bool:
        """
        用户注销
        
        Args:
            jti: JWT ID
        
        Returns:
            是否注销成功
        """
        blacklisted_tokens.add(jti)
        return True
    
    @staticmethod
    def is_token_blacklisted(jti: str) -> bool:
        """检查token是否在黑名单中"""
        return jti in blacklisted_tokens
    
    @staticmethod
    def verify_admin_permission(user) -> bool:
        """验证管理员权限"""
        return user and user.role == 'admin'
    
    @staticmethod
    def validate_user_permission(user_id: int, current_user) -> bool:
        """
        验证用户权限(用户只能操作自己的数据，管理员可以操作所有数据)
        
        Args:
            user_id: 要操作的用户ID
            current_user: 当前登录用户
        
        Returns:
            是否有权限
        """
        if not current_user:
            return False
        
        # 管理员可以操作所有用户数据
        if current_user.role == 'admin':
            return True
        
        # 普通用户只能操作自己的数据
        return current_user.id == user_id
    
    @staticmethod
    def create_default_users():
        """创建默认用户"""
        from app.models import db
        
        # 创建管理员用户
        admin_user = UserService.create_user('admin', 'admin123', 'admin')
        if admin_user:
            admin_user.email = 'admin@example.com'
            admin_user.full_name = '系统管理员'
        
        # 创建普通用户
        regular_user = UserService.create_user('user', 'user123', 'user')
        if regular_user:
            regular_user.email = 'user@example.com'
            regular_user.full_name = '普通用户'
        
        if admin_user or regular_user:
            db.session.commit()
    
    @staticmethod
    def get_user_from_token(token: str) -> Optional[Any]:
        """
        从token获取用户信息
        
        Args:
            token: JWT token
        
        Returns:
            用户对象或None
        """
        try:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
            
            decoded = decode_token(token)
            username = decoded['sub']
            return UserService.get_user_by_username(username)
        except:
            return None