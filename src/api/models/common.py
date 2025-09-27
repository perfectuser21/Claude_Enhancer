"""
通用数据模型
============

定义通用的请求和响应模型
"""

from typing import Optional, List, Dict, Any, Generic, TypeVar
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

# 泛型类型变量
T = TypeVar("T")


class BaseResponse(BaseModel):
    """基础响应模型"""

    success: bool = Field(True, description="请求是否成功")
    message: Optional[str] = Field(None, description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间戳")


class ErrorResponse(BaseResponse):
    """错误响应模型"""

    success: bool = Field(False, description="请求失败")
    error_code: Optional[str] = Field(None, description="错误代码")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")


class PaginationParams(BaseModel):
    """分页参数"""

    page: int = Field(1, ge=1, description="页码，从1开始")
    size: int = Field(20, ge=1, le=100, description="每页大小，最大100")

    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.size


class PaginationMeta(BaseModel):
    """分页元信息"""

    page: int = Field(description="当前页码")
    size: int = Field(description="每页大小")
    total: int = Field(description="总记录数")
    pages: int = Field(description="总页数")
    has_next: bool = Field(description="是否有下一页")
    has_prev: bool = Field(description="是否有上一页")


class PaginatedResponse(BaseResponse, Generic[T]):
    """分页响应模型"""

    data: List[T] = Field(description="数据列表")
    meta: PaginationMeta = Field(description="分页信息")


class FilterParams(BaseModel):
    """通用过滤参数"""

    search: Optional[str] = Field(None, description="搜索关键词")
    sort_by: Optional[str] = Field(None, description="排序字段")
    sort_order: Optional[str] = Field("asc", regex="^(asc|desc)$", description="排序方向")
    created_after: Optional[datetime] = Field(None, description="创建时间筛选（之后）")
    created_before: Optional[datetime] = Field(None, description="创建时间筛选（之前）")


class StatusResponse(BaseModel):
    """状态响应模型"""

    status: str = Field(description="状态")
    data: Optional[Dict[str, Any]] = Field(None, description="状态数据")


class BulkOperationRequest(BaseModel):
    """批量操作请求"""

    ids: List[UUID] = Field(..., min_items=1, description="操作对象ID列表")
    action: str = Field(..., description="操作类型")
    params: Optional[Dict[str, Any]] = Field(None, description="操作参数")


class BulkOperationResponse(BaseResponse):
    """批量操作响应"""

    total: int = Field(description="总操作数量")
    success_count: int = Field(description="成功数量")
    failure_count: int = Field(description="失败数量")
    results: List[Dict[str, Any]] = Field(description="详细结果")


class FileUploadResponse(BaseResponse):
    """文件上传响应"""

    file_id: UUID = Field(description="文件ID")
    filename: str = Field(description="文件名")
    file_size: int = Field(description="文件大小")
    file_url: str = Field(description="文件访问URL")


class HealthCheckResponse(BaseModel):
    """健康检查响应"""

    status: str = Field(description="服务状态")
    service: str = Field(description="服务名称")
    version: str = Field(description="服务版本")
    timestamp: datetime = Field(description="检查时间")
    environment: str = Field(description="运行环境")
    checks: Dict[str, str] = Field(default_factory=dict, description="各组件状态")
