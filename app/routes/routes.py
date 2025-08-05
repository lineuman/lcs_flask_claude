# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, send_file
from flask_jwt_extended import jwt_required, get_jwt
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.converter_service import ConverterService
from app.services.storage_service import StorageService
from app.services.user_variable_service import UserVariableService

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

# 文件管理页面
@main_bp.route('/files', methods=['GET'])
def files_page():
    return render_template('files.html')

# 文件上传API
@main_bp.route('/api/files/upload', methods=['POST'])
@jwt_required()
def upload_file():
    current_user = AuthService.get_current_user()
    
    if not current_user:
        return jsonify({"message": "用户不存在"}), 404
    
    if 'file' not in request.files:
        return jsonify({"message": "没有选择文件"}), 400
    
    file = request.files['file']
    description = request.form.get('description', '')
    
    try:
        storage_service = StorageService()
        result = storage_service.upload_file(file, current_user, description)
        
        return jsonify({
            "message": "文件上传成功",
            "file": result
        })
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": f"文件上传失败: {str(e)}"}), 500

# 获取用户文件列表API
@main_bp.route('/api/files', methods=['GET'])
@jwt_required()
def get_user_files():
    current_user = AuthService.get_current_user()
    
    if not current_user:
        return jsonify({"message": "用户不存在"}), 404
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    try:
        storage_service = StorageService()
        result = storage_service.get_user_files(current_user, page, per_page)
        
        return jsonify({
            "files": [file.to_dict() for file in result['files']],
            "pagination": {
                "total": result['total'],
                "page": result['page'],
                "per_page": result['per_page'],
                "total_pages": result['total_pages']
            }
        })
    except Exception as e:
        return jsonify({"message": f"获取文件列表失败: {str(e)}"}), 500

# 文件下载API
@main_bp.route('/api/files/<int:file_id>/download', methods=['GET'])
@jwt_required()
def download_file(file_id):
    current_user = AuthService.get_current_user()
    
    if not current_user:
        return jsonify({"message": "用户不存在"}), 404
    
    try:
        storage_service = StorageService()
        file_path = storage_service.download_file(file_id, current_user)
        
        if not file_path:
            return jsonify({"message": "文件不存在或无权限"}), 404
        
        # 增加下载次数
        storage_service.increment_download_count(file_id)
        
        # 获取文件信息
        stored_file = storage_service.get_file_by_id(file_id)
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=stored_file.original_filename,
            mimetype=stored_file.file_type
        )
    except Exception as e:
        return jsonify({"message": f"文件下载失败: {str(e)}"}), 500

# 删除文件API
@main_bp.route('/api/files/<int:file_id>', methods=['DELETE'])
@jwt_required()
def delete_file(file_id):
    current_user = AuthService.get_current_user()
    
    if not current_user:
        return jsonify({"message": "用户不存在"}), 404
    
    try:
        storage_service = StorageService()
        storage_service.delete_file(file_id, current_user)
        
        return jsonify({"message": "文件删除成功"})
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": f"文件删除失败: {str(e)}"}), 500

# 更新文件描述API
@main_bp.route('/api/files/<int:file_id>/description', methods=['PUT'])
@jwt_required()
def update_file_description(file_id):
    current_user = AuthService.get_current_user()
    
    if not current_user:
        return jsonify({"message": "用户不存在"}), 404
    
    data = request.get_json()
    description = data.get('description', '')
    
    try:
        storage_service = StorageService()
        storage_service.update_file_description(file_id, current_user, description)
        
        return jsonify({"message": "文件描述更新成功"})
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": f"文件描述更新失败: {str(e)}"}), 500

# 获取文件信息API
@main_bp.route('/api/files/<int:file_id>', methods=['GET'])
@jwt_required()
def get_file_info(file_id):
    current_user = AuthService.get_current_user()
    
    if not current_user:
        return jsonify({"message": "用户不存在"}), 404
    
    try:
        storage_service = StorageService()
        file_info = storage_service.get_file_info(file_id, current_user)
        
        if not file_info:
            return jsonify({"message": "文件不存在或无权限"}), 404
        
        return jsonify(file_info)
    except Exception as e:
        return jsonify({"message": f"获取文件信息失败: {str(e)}"}), 500

# 获取存储统计信息API
@main_bp.route('/api/files/stats', methods=['GET'])
@jwt_required()
def get_storage_stats():
    current_user = AuthService.get_current_user()
    
    if not current_user:
        return jsonify({"message": "用户不存在"}), 404
    
    try:
        storage_service = StorageService()
        stats = storage_service.get_storage_stats(current_user)
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({"message": f"获取存储统计信息失败: {str(e)}"}), 500
    

# 变量管理API端点
@main_bp.route('/variables', methods=['GET'])
def variables_page():
    """变量管理页面"""
    return render_template('variables.html')

@main_bp.route('/api/variables', methods=['GET'])
@jwt_required()
def api_get_user_variables():
    """获取用户所有变量"""
    current_user = AuthService.get_current_user()
    
    if not current_user:
        return jsonify({"message": "用户不存在"}), 404
    
    try:
        variables = UserVariableService.get_user_variables(current_user.id)
        # 使用to_dict方法转换为字典列表以便JSON序列化
        variables_list = [var.to_dict() for var in variables]
        return jsonify(variables_list)
    except Exception as e:
        return jsonify({"message": f"获取用户变量失败: {str(e)}"}), 500

@main_bp.route('/api/variables', methods=['POST'])
@jwt_required()
def api_create_user_variable():
    """创建用户变量"""
    current_user = AuthService.get_current_user()
    
    if not current_user:
        return jsonify({"message": "用户不存在"}), 404
    
    try:
        data = request.get_json()
        variable_name = data.get('variable_name')
        variable_value = data.get('variable_value')
        
        if not variable_name or not variable_value:
            return jsonify({"message": "变量名和变量值不能为空"}), 400
        
        # 检查变量名是否已存在
        existing_variable = UserVariableService.get_variable_by_name(current_user.id, variable_name)
        if existing_variable:
            return jsonify({"message": "变量名已存在"}), 400
        
        variable = UserVariableService.create_variable(
            user_id=current_user.id,
            variable_name=variable_name,
            variable_value=variable_value
        )
        
        if variable:
            return jsonify({
                "message": "变量创建成功",
                "variable": {
                    "id": variable.id,
                    "user_id": variable.user_id,
                    "variable_name": variable.variable_name,
                    "variable_value": variable.variable_value,
                    "created_at": variable.created_at.isoformat() if variable.created_at else None
                }
            }), 201
        else:
            return jsonify({"message": "变量创建失败"}), 500
    except Exception as e:
        return jsonify({"message": f"创建变量失败: {str(e)}"}), 500

@main_bp.route('/api/variables/<int:variable_id>', methods=['PUT'])
@jwt_required()
def api_update_user_variable(variable_id):
    """更新用户变量"""
    current_user = AuthService.get_current_user()
    
    if not current_user:
        return jsonify({"message": "用户不存在"}), 404
    
    try:
        data = request.get_json()
        variable_value = data.get('variable_value')
        variable_name = data.get('variable_name')
        
        if not variable_value:
            return jsonify({"message": "变量值不能为空"}), 400
        
        # 检查变量是否存在
        variable = UserVariableService.get_variable_by_id(variable_id)
        if not variable:
            return jsonify({"message": "变量不存在"}), 404
        
        # 检查是否是当前用户的变量
        if variable.user_id != current_user.id:
            return jsonify({"message": "无权限操作此变量"}), 403
        
        # 如果要更新变量名，检查新名称是否已存在
        if variable_name and variable_name != variable.variable_name:
            existing_variable = UserVariableService.get_variable_by_name(current_user.id, variable_name)
            if existing_variable:
                return jsonify({"message": "变量名已存在"}), 400
            # 更新变量名
            variable.variable_name = variable_name
        
        # 更新变量值
        updated_variable = UserVariableService.update_variable(variable_id, variable_value)
        
        if updated_variable:
            return jsonify({
                "message": "变量更新成功",
                "variable": {
                    "id": updated_variable.id,
                    "user_id": updated_variable.user_id,
                    "variable_name": updated_variable.variable_name,
                    "variable_value": updated_variable.variable_value,
                    "created_at": updated_variable.created_at.isoformat() if updated_variable.created_at else None
                }
            })
        else:
            return jsonify({"message": "变量更新失败"}), 500
    except Exception as e:
        return jsonify({"message": f"更新变量失败: {str(e)}"}), 500

@main_bp.route('/api/variables/<int:variable_id>', methods=['DELETE'])
@jwt_required()
def api_delete_user_variable(variable_id):
    """删除用户变量"""
    current_user = AuthService.get_current_user()
    
    if not current_user:
        return jsonify({"message": "用户不存在"}), 404
    
    try:
        # 检查变量是否存在
        variable = UserVariableService.get_variable_by_id(variable_id)
        if not variable:
            return jsonify({"message": "变量不存在"}), 404
        
        # 检查是否是当前用户的变量
        if variable.user_id != current_user.id:
            return jsonify({"message": "无权限操作此变量"}), 403
        
        # 删除变量
        result = UserVariableService.delete_variable(variable_id)
        
        if result:
            return jsonify({"message": "变量删除成功"})
        else:
            return jsonify({"message": "变量删除失败"}), 500
    except Exception as e:
        return jsonify({"message": f"删除变量失败: {str(e)}"}), 500

# 用户变量管理路由
@main_bp.route('/variables', methods=['GET'])
@jwt_required()
def get_user_variables():
    current_user = AuthService.get_current_user()
    
    if not current_user:
        return jsonify({"message": "用户不存在"}), 404
    
    try:
        variables = UserVariableService.get_user_variables(current_user.id)
        return jsonify(variables)
    except Exception as e:
        return jsonify({"message": f"获取用户变量失败: {str(e)}"}), 500