# -*- coding: utf-8 -*-
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from app.config import config
from app.models import db
from app.services.auth_service import jwt
from app.routes import main_bp

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    db.init_app(app)
    jwt.init_app(app)
    
    # 注册蓝图
    app.register_blueprint(main_bp)
    
    # 初始化数据库和创建默认用户
    def init_db():
        with app.app_context():
            db.create_all()
            
            # 导入AuthService并创建默认用户
            from app.services.auth_service import AuthService
            
            # 创建默认用户
            AuthService.create_default_users()
    
    # 初始化数据库
    with app.app_context():
        init_db()
    
    return app