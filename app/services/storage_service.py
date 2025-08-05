import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from werkzeug.datastructures import FileStorage
from app.models import db, User

class StorageService:
    """对象存储服务"""
    
    def __init__(self, upload_folder: str = 'uploads', max_file_size: int = 10 * 1024 * 1024):
        """
        初始化存储服务
        
        Args:
            upload_folder: 上传文件存储目录
            max_file_size: 最大文件大小（字节）
        """
        self.upload_folder = upload_folder
        self.max_file_size = max_file_size
        self.allowed_extensions = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'}
        
        # 确保上传目录存在
        os.makedirs(self.upload_folder, exist_ok=True)
        
    def _allowed_file(self, filename: str) -> bool:
        """检查文件扩展名是否允许"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def _generate_unique_filename(self, original_filename: str) -> str:
        """生成唯一文件名"""
        ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{timestamp}_{unique_id}.{ext}" if ext else f"{timestamp}_{unique_id}"
    
    def upload_file(self, file: FileStorage, user: User, description: str = "") -> Dict[str, Any]:
        """
        上传文件
        
        Args:
            file: 文件对象
            user: 上传用户
            description: 文件描述
        
        Returns:
            上传结果字典
        """
        if not file or not file.filename:
            raise ValueError("没有选择文件")
        
        if not self._allowed_file(file.filename):
            raise ValueError(f"不支持的文件类型，支持的类型：{', '.join(self.allowed_extensions)}")
        
        if file.content_length > self.max_file_size:
            raise ValueError(f"文件大小超过限制（最大 {self.max_file_size / (1024 * 1024):.1f}MB）")
        
        try:
            # 生成唯一文件名
            original_filename = file.filename
            unique_filename = self._generate_unique_filename(original_filename)
            
            # 创建用户专属目录
            user_folder = os.path.join(self.upload_folder, str(user.id))
            os.makedirs(user_folder, exist_ok=True)
            
            # 保存文件
            file_path = os.path.join(user_folder, unique_filename)
            file.save(file_path)
            
            # 获取文件信息
            file_size = os.path.getsize(file_path)
            file_type = file.content_type or 'application/octet-stream'
            
            # 创建文件记录
            from app.models import StoredFile
            stored_file = StoredFile(
                user_id=user.id,
                original_filename=original_filename,
                stored_filename=unique_filename,
                file_path=file_path,
                file_size=file_size,
                file_type=file_type,
                description=description
            )
            
            db.session.add(stored_file)
            db.session.commit()
            
            return {
                'success': True,
                'file_id': stored_file.id,
                'filename': original_filename,
                'file_size': file_size,
                'file_type': file_type,
                'upload_time': stored_file.upload_time
            }
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def get_file_by_id(self, file_id: int) -> Optional[Any]:
        """根据ID获取文件记录"""
        from app.models import StoredFile
        return StoredFile.query.get(file_id)
    
    def get_user_files(self, user: User, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        获取用户的文件列表
        
        Args:
            user: 用户对象
            page: 页码
            per_page: 每页数量
        
        Returns:
            文件列表和分页信息
        """
        from app.models import StoredFile
        
        # 获取总数
        total_files = StoredFile.query.filter_by(user_id=user.id).count()
        
        # 获取分页数据
        files = StoredFile.query.filter_by(user_id=user.id)\
            .order_by(StoredFile.upload_time.desc())\
            .offset((page - 1) * per_page)\
            .limit(per_page)\
            .all()
        
        return {
            'files': files,
            'total': total_files,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_files + per_page - 1) // per_page
        }
    
    def download_file(self, file_id: int, user: User) -> Optional[str]:
        """
        下载文件
        
        Args:
            file_id: 文件ID
            user: 用户对象
        
        Returns:
            文件路径或None（如果文件不存在或无权限）
        """
        stored_file = self.get_file_by_id(file_id)
        
        if not stored_file:
            return None
        
        if stored_file.user_id != user.id:
            return None
        
        if not os.path.exists(stored_file.file_path):
            return None
        
        return stored_file.file_path
    
    def delete_file(self, file_id: int, user: User) -> bool:
        """
        删除文件
        
        Args:
            file_id: 文件ID
            user: 用户对象
        
        Returns:
            是否删除成功
        """
        try:
            stored_file = self.get_file_by_id(file_id)
            
            if not stored_file:
                raise ValueError("文件不存在")
            
            if stored_file.user_id != user.id:
                raise ValueError("无权限删除此文件")
            
            # 删除物理文件
            if os.path.exists(stored_file.file_path):
                os.remove(stored_file.file_path)
            
            # 删除数据库记录
            db.session.delete(stored_file)
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def update_file_description(self, file_id: int, user: User, description: str) -> bool:
        """
        更新文件描述
        
        Args:
            file_id: 文件ID
            user: 用户对象
            description: 新描述
        
        Returns:
            是否更新成功
        """
        try:
            stored_file = self.get_file_by_id(file_id)
            
            if not stored_file:
                raise ValueError("文件不存在")
            
            if stored_file.user_id != user.id:
                raise ValueError("无权限修改此文件")
            
            stored_file.description = description
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def get_file_info(self, file_id: int, user: User) -> Optional[Dict[str, Any]]:
        """
        获取文件信息
        
        Args:
            file_id: 文件ID
            user: 用户对象
        
        Returns:
            文件信息字典或None
        """
        stored_file = self.get_file_by_id(file_id)
        
        if not stored_file or stored_file.user_id != user.id:
            return None
        
        return {
            'id': stored_file.id,
            'original_filename': stored_file.original_filename,
            'file_size': stored_file.file_size,
            'file_type': stored_file.file_type,
            'description': stored_file.description,
            'upload_time': stored_file.upload_time,
            'download_count': stored_file.download_count
        }
    
    def get_storage_stats(self, user: User) -> Dict[str, Any]:
        """
        获取用户存储统计信息
        
        Args:
            user: 用户对象
        
        Returns:
            存储统计信息
        """
        from app.models import StoredFile
        
        # 获取用户所有文件
        files = StoredFile.query.filter_by(user_id=user.id).all()
        
        total_files = len(files)
        total_size = sum(f.file_size for f in files)
        total_downloads = sum(f.download_count for f in files)
        
        # 计算文件类型分布
        type_stats = {}
        for file in files:
            file_type = file.file_type.split('/')[0] if '/' in file.file_type else file.file_type
            type_stats[file_type] = type_stats.get(file_type, 0) + 1
        
        return {
            'total_files': total_files,
            'total_size': total_size,
            'total_downloads': total_downloads,
            'type_distribution': type_stats,
            'storage_limit': self.max_file_size * 100,  # 假设每个用户最多100个文件
            'storage_used': total_size
        }
    
    def increment_download_count(self, file_id: int) -> bool:
        """
        增加文件下载次数
        
        Args:
            file_id: 文件ID
        
        Returns:
            是否成功
        """
        try:
            stored_file = self.get_file_by_id(file_id)
            
            if not stored_file:
                return False
            
            stored_file.download_count += 1
            db.session.commit()
            
            return True
            
        except Exception:
            db.session.rollback()
            return False