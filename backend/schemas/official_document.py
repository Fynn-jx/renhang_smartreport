"""
公文库 Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class DocumentSource(str, Enum):
    """公文来源机构枚举"""
    世界银行 = "世界银行"
    IMF = "IMF"
    联合国 = "联合国"
    联合国非洲经济委员会 = "联合国非洲经济委员会"
    非洲开发银行 = "非洲开发银行"
    WTO = "WTO"
    OECD = "OECD"
    中国人民银行 = "中国人民银行"
    国家统计局 = "国家统计局"
    其他 = "其他"


# ==================== Request Schemas ====================

class OfficialDocumentCreate(BaseModel):
    """创建公文"""
    title: str = Field(..., min_length=1, max_length=500, description="公文标题")
    description: Optional[str] = Field(None, description="公文描述")
    source: DocumentSource = Field(..., description="来源机构")
    is_verified: bool = Field(False, description="是否已审核")


class OfficialDocumentUpdate(BaseModel):
    """更新公文"""
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="公文标题")
    description: Optional[str] = Field(None, description="公文描述")
    source: Optional[DocumentSource] = Field(None, description="来源机构")
    is_verified: Optional[bool] = Field(None, description="是否已审核")


class OfficialDocumentListQuery(BaseModel):
    """公文列表查询参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    source: Optional[str] = Field(None, description="按来源机构筛选")
    keyword: Optional[str] = Field(None, description="按关键词搜索")
    is_verified: Optional[bool] = Field(None, description="按审核状态筛选")
    sort_by: str = Field("created_at", description="排序字段")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="排序方向")


# ==================== Response Schemas ====================

class OfficialDocumentBase(BaseModel):
    """公文基础信息"""
    id: str
    title: str
    original_filename: str
    document_type: str
    description: Optional[str] = None
    source: str
    file_size: int
    mime_type: str
    upload_date: str  # 上传日期（YYYY-MM-DD 格式）
    is_verified: bool = False
    verified_by: Optional[str] = None
    verified_at: Optional[int] = None  # Unix 时间戳
    page_count: Optional[int] = None
    content_preview: Optional[str] = None
    content: Optional[str] = None  # 添加完整内容字段

    class Config:
        from_attributes = True


class OfficialDocumentResponse(OfficialDocumentBase):
    """公文响应"""
    file_path: str
    thumbnail_path: Optional[str] = None
    created_at: int  # Unix 时间戳
    updated_at: int  # Unix 时间戳

    @classmethod
    def from_orm_obj(cls, obj):
        """从 ORM 对象创建响应"""
        # 将 Unix 时间戳转换为 YYYY-MM-DD 格式
        upload_date = datetime.fromtimestamp(obj.created_at).strftime("%Y-%m-%d")

        return cls(
            id=str(obj.id),
            title=obj.title,
            original_filename=obj.original_filename,
            document_type=obj.document_type,
            description=obj.description,
            source=obj.source,
            file_size=obj.file_size,
            mime_type=obj.mime_type,
            upload_date=upload_date,
            is_verified=obj.is_verified,
            verified_by=str(obj.verified_by) if obj.verified_by else None,
            verified_at=obj.verified_at,
            page_count=obj.page_count,
            content_preview=obj.content_preview,
            content=obj.content,  # 添加完整内容
            file_path=obj.file_path,
            thumbnail_path=obj.thumbnail_path,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )


class OfficialDocumentUploadResponse(BaseModel):
    """公文上传响应"""
    document_id: str
    filename: str
    file_size: int
    document_type: str
    message: str


class OfficialDocumentContentResponse(BaseModel):
    """公文内容响应"""
    content: Optional[str] = None
    content_preview: Optional[str] = None
    page_count: Optional[int] = None
