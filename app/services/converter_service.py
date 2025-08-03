from app.models import db, ConversionResult
from app.converter import convert_curl_to_python
from typing import List, Dict, Any, Optional
from datetime import datetime

class ConverterService:
    @staticmethod
    def convert_curl_command(curl_command: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        转换curl命令为Python代码并保存结果
        
        Args:
            curl_command: curl命令
            user_id: 用户ID(可选)
        
        Returns:
            转换结果字典
        """
        try:
            # 执行转换
            python_code = convert_curl_to_python(curl_command)
            
            # 创建转换结果记录
            result = ConversionResult(
                user_id=user_id,
                curl_command=curl_command,
                python_code=python_code,
                status='转换成功'
            )
            db.session.add(result)
            db.session.commit()
            
            return {
                'success': True,
                'curl': curl_command,
                'python': python_code,
                'status': 'converted',
                'message': '转换成功'
            }
            
        except Exception as e:
            # 创建错误记录
            error_result = ConversionResult(
                user_id=user_id,
                curl_command=curl_command,
                python_code=f'转换错误: {str(e)}',
                status='转换失败'
            )
            db.session.add(error_result)
            db.session.commit()
            
            return {
                'success': False,
                'curl': curl_command,
                'python': f'# 转换错误: {str(e)}',
                'status': 'error',
                'message': f'转换失败: {str(e)}'
            }
    
    @staticmethod
    def get_conversion_history(limit: int = 20, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取转换历史记录
        
        Args:
            limit: 限制记录数量
            user_id: 用户ID(可选，如果提供则只返回该用户的记录)
        
        Returns:
            转换历史记录列表
        """
        query = ConversionResult.query
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        results = query.order_by(ConversionResult.created_at.desc()).limit(limit).all()
        
        return [{
            'id': r.id,
            'curl': r.curl_command,
            'python': r.python_code,
            'status': r.status,
            'created_at': r.created_at.isoformat() if r.created_at else None
        } for r in results]
    
    @staticmethod
    def get_conversion_by_id(conversion_id: int) -> Optional[ConversionResult]:
        """根据ID获取转换结果"""
        return ConversionResult.query.get(conversion_id)
    
    @staticmethod
    def get_user_conversions(user_id: int, limit: int = 50) -> List[ConversionResult]:
        """获取用户的转换记录"""
        return ConversionResult.query.filter_by(user_id=user_id)\
            .order_by(ConversionResult.created_at.desc())\
            .limit(limit)\
            .all()
    
    @staticmethod
    def delete_conversion(conversion_id: int, user_id: Optional[int] = None) -> bool:
        """
        删除转换记录
        
        Args:
            conversion_id: 转换记录ID
            user_id: 用户ID(可选，用于验证权限)
        
        Returns:
            是否删除成功
        """
        try:
            conversion = ConverterService.get_conversion_by_id(conversion_id)
            if not conversion:
                return False
            
            # 如果提供了user_id，验证权限
            if user_id is not None and conversion.user_id != user_id:
                return False
            
            db.session.delete(conversion)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def get_conversion_stats(user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        获取转换统计信息
        
        Args:
            user_id: 用户ID(可选)
        
        Returns:
            统计信息字典
        """
        query = ConversionResult.query
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        total = query.count()
        successful = query.filter_by(status='转换成功').count()
        failed = query.filter_by(status='转换失败').count()
        
        return {
            'total_conversions': total,
            'successful_conversions': successful,
            'failed_conversions': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0
        }
    
    @staticmethod
    def validate_curl_command(curl_command: str) -> bool:
        """
        验证curl命令格式
        
        Args:
            curl_command: curl命令
        
        Returns:
            是否为有效的curl命令
        """
        curl_command = curl_command.strip()
        if not curl_command.startswith('curl'):
            return False
        
        # 基本格式检查
        import re
        url_match = re.search(r'curl\s+["\']?([^"\'\s]+)', curl_command)
        return bool(url_match)