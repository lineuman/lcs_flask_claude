#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service层功能测试脚本
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.services.converter_service import ConverterService

def test_user_service():
    """测试UserService功能"""
    print("=== 测试 UserService ===")
    
    # 创建测试用户
    test_user = UserService.create_user('testuser', 'test123', 'user', 
                                       email='test@example.com', full_name='测试用户')
    if test_user:
        print(f"✓ 用户创建成功: {test_user.username}")
    else:
        print("✗ 用户创建失败")
        return False
    
    # 测试用户查询
    user = UserService.get_user_by_username('testuser')
    if user:
        print(f"✓ 用户查询成功: {user.username}")
    else:
        print("✗ 用户查询失败")
        return False
    
    # 测试密码验证
    if UserService.verify_password(user, 'test123'):
        print("✓ 密码验证成功")
    else:
        print("✗ 密码验证失败")
        return False
    
    # 测试用户资料更新
    try:
        UserService.update_user_profile(user, full_name='更新后的用户名', phone='1234567890')
        print("✓ 用户资料更新成功")
    except Exception as e:
        print(f"✗ 用户资料更新失败: {e}")
        return False
    
    # 测试密码修改
    try:
        UserService.change_password(user, 'test123', 'newpassword123')
        print("✓ 密码修改成功")
    except Exception as e:
        print(f"✗ 密码修改失败: {e}")
        return False
    
    # 删除测试用户
    try:
        UserService.delete_user(user)
        print("✓ 用户删除成功")
    except Exception as e:
        print(f"✗ 用户删除失败: {e}")
        return False
    
    return True

def test_auth_service():
    """测试AuthService功能"""
    print("\n=== 测试 AuthService ===")
    
    # 创建测试用户
    test_user = UserService.create_user('authtest', 'auth123', 'user')
    if test_user:
        from app.models import db
        db.session.commit()
        print(f"✓ 测试用户创建成功: {test_user.username}")
    else:
        print("✗ 测试用户创建失败")
        return False
    
    # 测试用户认证
    auth_result = AuthService.authenticate_user('authtest', 'auth123')
    if auth_result:
        print("✓ 用户认证成功")
        print(f"  Token: {auth_result['access_token'][:20]}...")
        print(f"  User: {auth_result['user']['username']}")
    else:
        print("✗ 用户认证失败")
        return False
    
    # 测试错误密码
    wrong_auth = AuthService.authenticate_user('authtest', 'wrongpassword')
    if not wrong_auth:
        print("✓ 错误密码认证失败（符合预期）")
    else:
        print("✗ 错误密码认证应该失败")
        return False
    
    # 清理测试用户
    try:
        UserService.delete_user(test_user)
        print("✓ 测试用户清理成功")
    except Exception as e:
        print(f"✗ 测试用户清理失败: {e}")
        return False
    
    return True

def test_converter_service():
    """测试ConverterService功能"""
    print("\n=== 测试 ConverterService ===")
    
    # 测试curl转换
    curl_command = 'curl -X POST https://api.example.com/users -H "Content-Type: application/json" -d \'{"name": "John", "email": "john@example.com"}\''
    
    result = ConverterService.convert_curl_command(curl_command)
    if result['success']:
        print("✓ curl转换成功")
        print(f"  Status: {result['status']}")
        print(f"  Python代码长度: {len(result['python'])}")
    else:
        print(f"✗ curl转换失败: {result['message']}")
        return False
    
    # 测试无效curl命令
    invalid_result = ConverterService.convert_curl_command('invalid command')
    if not invalid_result['success']:
        print("✓ 无效curl命令转换失败（符合预期）")
    else:
        print("✗ 无效curl命令转换应该失败")
        return False
    
    # 测试转换历史查询
    history = ConverterService.get_conversion_history(limit=5)
    print(f"✓ 转换历史查询成功，返回 {len(history)} 条记录")
    
    # 测试转换统计
    stats = ConverterService.get_conversion_stats()
    print(f"✓ 转换统计查询成功: {stats}")
    
    # 测试curl命令验证
    valid_curl = 'curl https://example.com'
    invalid_curl = 'invalid command'
    
    if ConverterService.validate_curl_command(valid_curl):
        print("✓ 有效curl命令验证成功")
    else:
        print("✗ 有效curl命令验证失败")
        return False
    
    if not ConverterService.validate_curl_command(invalid_curl):
        print("✓ 无效curl命令验证失败（符合预期）")
    else:
        print("✗ 无效curl命令验证应该失败")
        return False
    
    return True

def main():
    """主测试函数"""
    print("开始Service层功能测试...")
    
    with create_app().app_context():
        # 测试各个service
        user_test = test_user_service()
        auth_test = test_auth_service()
        converter_test = test_converter_service()
        
        print("\n=== 测试结果 ===")
        print(f"UserService测试: {'✓ 通过' if user_test else '✗ 失败'}")
        print(f"AuthService测试: {'✓ 通过' if auth_test else '✗ 失败'}")
        print(f"ConverterService测试: {'✓ 通过' if converter_test else '✗ 失败'}")
        
        if user_test and auth_test and converter_test:
            print("\n🎉 所有测试通过！Service层功能正常。")
            return True
        else:
            print("\n❌ 部分测试失败，请检查代码。")
            return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)