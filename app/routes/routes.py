# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.converter_service import ConverterService

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        curl_command = request.form.get('curl_command', '')
        if curl_command:
            # 获取当前用户
            current_user = None
            token = request.cookies.get('access_token') or request.headers.get('Authorization')
            if token:
                current_user = AuthService.get_user_from_token(token)
            
            user_id = current_user.id if current_user else None
            
            # 使用service层处理转换
            result = ConverterService.convert_curl_command(curl_command, user_id)
    
    # 获取最近的转换结果
    results = ConverterService.get_conversion_history(limit=20)
    return render_template('index.html', results=results)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    
    if not username or not password:
        return jsonify({"msg": "缺少用户名或密码"}), 400
    
    auth_result = AuthService.authenticate_user(username, password)
    if auth_result:
        return jsonify(auth_result)
    
    return jsonify({"msg": "用户名或密码错误"}), 401

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    
    if not username or not password:
        return jsonify({"msg": "缺少用户名或密码"}), 400
    
    register_result = AuthService.register_user(username, password)
    if register_result:
        return jsonify({"msg": "注册成功"}), 201
    
    return jsonify({"msg": "用户名已存在"}), 400

@main_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']
    AuthService.logout_user(jti)
    return jsonify({"msg": "注销成功"})

@main_bp.route('/protected')
@jwt_required()
def protected():
    current_user = AuthService.get_current_user()
    return jsonify({
        "msg": f"欢迎 {current_user.username}",
        "user": {
            "username": current_user.username,
            "role": current_user.role
        }
    })

@main_bp.route('/admin')
@jwt_required()
def admin():
    current_user = AuthService.get_current_user()
    
    if not AuthService.verify_admin_permission(current_user):
        return jsonify({"msg": "需要管理员权限"}), 403
    
    users = UserService.get_all_users()
    return jsonify({
        "msg": "管理员面板",
        "users": [user.username for user in users]
    })

@main_bp.route('/api/curl-convert', methods=['POST'])
@jwt_required()
def curl_convert():
    curl_command = request.json.get('curl_command', '')
    if not curl_command:
        return jsonify({"error": "缺少 curl 命令"}), 400
    
    user_id = AuthService.get_current_user_id()
    result = ConverterService.convert_curl_command(curl_command, user_id)
    
    if result['success']:
        return jsonify({
            "curl": result['curl'],
            "python": result['python'],
            "status": result['status']
        })
    else:
        return jsonify({
            "curl": result['curl'],
            "python": result['python'],
            "status": result['status']
        }), 400

# 用户信息管理路由
@main_bp.route('/profile', methods=['GET'])
def profile():
    return render_template('profile.html')

# 获取用户信息API
@main_bp.route('/api/user/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    current_user = AuthService.get_current_user()
    
    if not current_user:
        return jsonify({"message": "用户不存在"}), 404
    
    return jsonify(current_user.to_dict())

# 更新用户信息API
@main_bp.route('/api/user/profile', methods=['PUT'])
@jwt_required()
def update_user_profile():
    current_user = AuthService.get_current_user()
    
    if not current_user:
        return jsonify({"message": "用户不存在"}), 404
    
    data = request.get_json()
    
    try:
        UserService.update_user_profile(current_user, **data)
        return jsonify({
            "message": "个人信息更新成功",
            "user": current_user.to_dict()
        })
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": f"更新失败: {str(e)}"}), 500

# 修改密码API
@main_bp.route('/api/user/change-password', methods=['POST'])
@jwt_required()
def change_password():
    current_user = AuthService.get_current_user()
    
    if not current_user:
        return jsonify({"message": "用户不存在"}), 404
    
    data = request.get_json()
    
    # 验证必需字段
    if not data.get('current_password') or not data.get('new_password'):
        return jsonify({"message": "请提供当前密码和新密码"}), 400
    
    try:
        UserService.change_password(current_user, data['current_password'], data['new_password'])
        return jsonify({"message": "密码修改成功"})
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": f"密码修改失败: {str(e)}"}), 500