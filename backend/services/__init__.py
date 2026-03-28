"""
服务模块初始化
导出所有服务单例
"""

from services.file_service import file_service
from services.document_service import document_service
from services.image_translation_service import image_translation_service
from services.document_translation_service import document_translation_service
from services.academic_to_official_service import academic_to_official_service

__all__ = [
    "file_service",
    "document_service",
    "image_translation_service",
    "document_translation_service",
    "academic_to_official_service",
]
