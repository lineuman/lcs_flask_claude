import bcrypt
from app.models import db, User
from typing import Optional, Dict, Any

class UserService:
    @staticmethod
    def create_user(username: str, password: str, role: str = 'user', **kwargs) -> Optional[User]:
        """
        创建新用户
        
        Args:
            username: 用户名
            password: 密码
            role: 用户角色
            **kwargs: 其他用户信息(email, full_name, phone, avatar_url, bio)
        
        Returns:
            User对象或None(如果用户名已存在)
        """
        if UserService.get_user_by_username(username):
            return None
        
        new_user = User(
            username=username,
            password=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()),
            role=role,
            **kwargs
        )
        db.session.add(new_user)
        return new_user
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return User.query.get(user_id)
    
    @staticmethod
    def get_all_users() -> list[User]:
        """获取所有用户"""
        return User.query.all()
    
    @staticmethod
    def update_user_profile(user: User, **kwargs) -> bool:
        """
        更新用户资料
        
        Args:
            user: 用户对象
            **kwargs: 要更新的字段
        
        Returns:
            是否更新成功
        """
        try:
            # 检查邮箱是否已被其他用户使用
            if 'email' in kwargs and kwargs['email'] and kwargs['email'] != user.email:
                existing_user = UserService.get_user_by_email(kwargs['email'])
                if existing_user and existing_user.id != user.id:
                    raise ValueError("邮箱已被其他用户使用")
            
            # 更新字段
            for key, value in kwargs.items():
                if hasattr(user, key) and key not in ['id', 'username', 'password', 'role']:
                    setattr(user, key, value)
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def change_password(user: User, current_password: str, new_password: str) -> bool:
        """
        修改用户密码
        
        Args:
            user: 用户对象
            current_password: 当前密码
            new_password: 新密码
        
        Returns:
            是否修改成功
        """
        if not bcrypt.checkpw(current_password.encode('utf-8'), user.password):
            raise ValueError("当前密码错误")
        
        if len(new_password) < 6:
            raise ValueError("新密码长度至少6位")
        
        try:
            user.password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def verify_password(user: User, password: str) -> bool:
        """验证用户密码"""
        return bcrypt.checkpw(password.encode('utf-8'), user.password)
    
    @staticmethod
    def delete_user(user: User) -> bool:
        """删除用户"""
        try:
            db.session.delete(user)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e