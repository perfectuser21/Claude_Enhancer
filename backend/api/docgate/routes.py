"""
DocGate Agent API路由实现
提供完整的文档质量管理API端点
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    status,
    BackgroundTasks,
)
from fastapi.responses import FileResponse, StreamingResponse
from typing import Dict, Any, List, Optional, Union
import logging
from datetime import datetime, timedelta
import uuid
import os
from pathlib import Path

# 导入模型
from .models import (
    # 请求模型
    QualityCheckRequest,
    BatchQualityCheckRequest,
    ConfigCreateRequest,
    WebhookCreateRequest,
    # 响应模型
    QualityCheckResponse,
    BatchQualityCheckResponse,
    QualityReport,
    ConfigResponse,
    WebhookResponse,
    SystemHealth,
    UsageStats,
    ApiResponse,
    ApiError,
    PaginatedResponse,
    # 枚举
    CheckStatus,
    Priority,
    WebhookEvent,
)

# 导入依赖和服务
from backend.api.auth.dependencies import (
    get_current_active_user,
    require_permissions,
    get_client_info,
    rate_limit_check,
)
from backend.core.models import User
from backend.core.monitoring import monitor_endpoint, SecurityEvent


# DocGate服务（假设存在这些服务类）
# 在实际实现中需要创建这些服务类
class DocGateService:
    """文档质量检查服务"""

    async def submit_check(
        self, user_id: str, request: QualityCheckRequest
    ) -> QualityCheckResponse:
        """提交质量检查任务"""
        # 实现质量检查逻辑
        pass

    async def submit_batch_check(
        self, user_id: str, request: BatchQualityCheckRequest
    ) -> BatchQualityCheckResponse:
        """提交批量质量检查任务"""
        pass

    async def get_check_status(
        self, check_id: str, user_id: str
    ) -> QualityCheckResponse:
        """获取检查状态"""
        pass

    async def cancel_check(self, check_id: str, user_id: str) -> bool:
        """取消检查任务"""
        pass

    async def get_report(self, check_id: str, user_id: str) -> QualityReport:
        """获取质量报告"""
        pass


class ConfigService:
    """配置管理服务"""

    async def get_configs(self, user_id: str) -> List[ConfigResponse]:
        """获取配置列表"""
        pass

    async def create_config(
        self, user_id: str, request: ConfigCreateRequest
    ) -> ConfigResponse:
        """创建配置"""
        pass

    async def update_config(
        self, config_id: str, user_id: str, request: ConfigCreateRequest
    ) -> ConfigResponse:
        """更新配置"""
        pass

    async def delete_config(self, config_id: str, user_id: str) -> bool:
        """删除配置"""
        pass


class WebhookService:
    """Webhook管理服务"""

    async def create_webhook(
        self, user_id: str, request: WebhookCreateRequest
    ) -> WebhookResponse:
        """创建Webhook"""
        pass

    async def get_webhooks(self, user_id: str) -> List[WebhookResponse]:
        """获取Webhook列表"""
        pass

    async def test_webhook(self, webhook_id: str, user_id: str) -> bool:
        """测试Webhook"""
        pass


# 依赖注入函数
async def get_docgate_service() -> DocGateService:
    """获取DocGate服务实例"""
    return DocGateService()


async def get_config_service() -> ConfigService:
    """获取配置服务实例"""
    return ConfigService()


async def get_webhook_service() -> WebhookService:
    """获取Webhook服务实例"""
    return WebhookService()


# 创建路由器
router = APIRouter(prefix="/v1/docgate", tags=["DocGate质量管理"])
logger = logging.getLogger(__name__)


# =============== 质量检查接口 ===============


@router.post(
    "/checks",
    response_model=ApiResponse[QualityCheckResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="提交文档质量检查",
    description="提交单个文档的质量检查任务",
    responses={
        202: {"description": "检查任务已提交"},
        400: {"model": ApiError, "description": "请求参数错误"},
        401: {"model": ApiError, "description": "未认证"},
        403: {"model": ApiError, "description": "权限不足"},
        429: {"model": ApiError, "description": "请求频率过高"},
    },
)
@monitor_endpoint("docgate_submit_check")
async def submit_quality_check(
    request: QualityCheckRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    client_info: Dict[str, Any] = Depends(get_client_info),
    docgate_service: DocGateService = Depends(get_docgate_service),
    _: bool = Depends(require_permissions(["docgate:write"])),
    __: bool = Depends(rate_limit_check),
) -> ApiResponse[QualityCheckResponse]:
    """
    ## 提交文档质量检查

    提交单个文档的质量检查任务，支持异步和同步模式。

    ### 支持的文档类型
    - Markdown (.md, .markdown)
    - HTML (.html, .htm)
    - 纯文本 (.txt)
    - reStructuredText (.rst)

    ### 检查项目
    - **语法检查**: 语法错误、标点符号
    - **拼写检查**: 单词拼写、术语一致性
    - **样式检查**: 格式规范、样式一致性
    - **结构检查**: 文档结构、标题层级
    - **链接检查**: 链接有效性、引用完整性
    - **图片检查**: 图片存在性、alt文本

    ### 异步处理
    当启用异步模式时，系统会立即返回检查ID，可通过状态查询接口获取进度。
    如果配置了Webhook，完成时会自动推送通知。
    """
    try:
        logger.info(f"用户 {current_user.id} 提交质量检查: {request.document_source.path}")

        # 记录安全事件
        SecurityEvent.log_security_event(
            event_type="docgate_check_submitted",
            user_id=str(current_user.id),
            ip_address=client_info["ip_address"],
            details={
                "document_path": request.document_source.path,
                "document_type": request.document_source.type.value,
                "async_mode": request.options.async_mode,
            },
        )

        # 提交检查任务
        result = await docgate_service.submit_check(
            user_id=str(current_user.id), request=request
        )

        logger.info(f"质量检查任务已提交: {result.check_id}")

        return ApiResponse(
            success=True,
            data=result,
            message="文档质量检查任务已提交",
            request_id=client_info.get("request_id"),
        )

    except ValueError as e:
        logger.warning(f"质量检查提交失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "DOC_VAL_001",
                "type": "VALIDATION_ERROR",
                "message": str(e),
            },
        )
    except Exception as e:
        logger.error(f"质量检查提交异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DOC_SER_002",
                "type": "SERVICE_ERROR",
                "message": "质量检查服务暂时不可用",
            },
        )


@router.post(
    "/checks/batch",
    response_model=ApiResponse[BatchQualityCheckResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="批量文档质量检查",
    description="提交多个文档的批量质量检查任务",
)
@monitor_endpoint("docgate_submit_batch_check")
async def submit_batch_quality_check(
    request: BatchQualityCheckRequest,
    current_user: User = Depends(get_current_active_user),
    client_info: Dict[str, Any] = Depends(get_client_info),
    docgate_service: DocGateService = Depends(get_docgate_service),
    _: bool = Depends(require_permissions(["docgate:write"])),
    __: bool = Depends(rate_limit_check),
) -> ApiResponse[BatchQualityCheckResponse]:
    """
    ## 批量文档质量检查

    一次提交多个文档的质量检查任务，支持并行处理。

    ### 批量限制
    - 最多50个文档/批次
    - 最大并发数: 10
    - 单个文档最大50MB

    ### 处理策略
    - **并行处理**: 同时处理多个文档
    - **容错机制**: 单个文档失败不影响其他文档
    - **进度跟踪**: 实时跟踪批次处理进度
    """
    try:
        logger.info(f"用户 {current_user.id} 提交批量质量检查: {len(request.documents)}个文档")

        # 验证文档数量限制
        if len(request.documents) > 50:
            raise ValueError("批量检查最多支持50个文档")

        # 提交批量检查
        result = await docgate_service.submit_batch_check(
            user_id=str(current_user.id), request=request
        )

        logger.info(f"批量质量检查任务已提交: {result.batch_id}")

        return ApiResponse(
            success=True,
            data=result,
            message=f"批量质量检查任务已提交，共{len(request.documents)}个文档",
            request_id=client_info.get("request_id"),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "DOC_VAL_004",
                "type": "VALIDATION_ERROR",
                "message": str(e),
            },
        )
    except Exception as e:
        logger.error(f"批量质量检查提交异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DOC_SER_002",
                "type": "SERVICE_ERROR",
                "message": "批量质量检查服务暂时不可用",
            },
        )


@router.get(
    "/checks/{check_id}",
    response_model=ApiResponse[QualityCheckResponse],
    summary="获取检查状态",
    description="获取指定检查任务的详细状态和进度信息",
)
@monitor_endpoint("docgate_get_check_status")
async def get_check_status(
    check_id: str,
    current_user: User = Depends(get_current_active_user),
    docgate_service: DocGateService = Depends(get_docgate_service),
    _: bool = Depends(require_permissions(["docgate:read"])),
) -> ApiResponse[QualityCheckResponse]:
    """
    ## 获取检查状态

    获取指定检查任务的详细状态信息，包括：
    - 任务状态和进度
    - 文档基本信息
    - 问题摘要（如果已完成）
    - 时间戳信息

    ### 状态说明
    - **queued**: 任务已排队等待处理
    - **running**: 任务正在执行中
    - **completed**: 任务已完成
    - **failed**: 任务执行失败
    - **cancelled**: 任务已取消
    """
    try:
        result = await docgate_service.get_check_status(
            check_id=check_id, user_id=str(current_user.id)
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "DOC_NOT_002",
                    "type": "NOT_FOUND",
                    "message": "检查任务不存在",
                },
            )

        return ApiResponse(success=True, data=result, message="检查状态获取成功")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取检查状态异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DOC_SER_001",
                "type": "SERVICE_ERROR",
                "message": "获取检查状态服务暂时不可用",
            },
        )


@router.get(
    "/checks",
    response_model=ApiResponse[PaginatedResponse],
    summary="获取检查列表",
    description="获取用户的检查任务列表，支持分页和过滤",
)
@monitor_endpoint("docgate_list_checks")
async def list_checks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    status: Optional[CheckStatus] = Query(None, description="状态过滤"),
    document_type: Optional[str] = Query(None, description="文档类型过滤"),
    created_from: Optional[datetime] = Query(None, description="创建时间起始"),
    created_to: Optional[datetime] = Query(None, description="创建时间结束"),
    sort: str = Query("created_at:desc", description="排序方式"),
    current_user: User = Depends(get_current_active_user),
    docgate_service: DocGateService = Depends(get_docgate_service),
    _: bool = Depends(require_permissions(["docgate:read"])),
) -> ApiResponse[PaginatedResponse]:
    """
    ## 获取检查列表

    分页获取用户的文档质量检查任务列表。

    ### 查询参数
    - **page**: 页码，从1开始
    - **page_size**: 每页大小，最大100
    - **status**: 状态过滤（queued|running|completed|failed|cancelled）
    - **document_type**: 文档类型过滤（md|html|txt|rst）
    - **created_from/to**: 时间范围过滤
    - **sort**: 排序方式（created_at:desc|asc, updated_at:desc|asc）

    ### 排序选项
    - `created_at:desc` - 按创建时间倒序（默认）
    - `created_at:asc` - 按创建时间正序
    - `updated_at:desc` - 按更新时间倒序
    - `score:desc` - 按质量评分倒序（仅已完成）
    """
    try:
        pass  # Auto-fixed empty block
        # 这里应该调用实际的服务方法来获取检查列表
        # 为示例目的，返回模拟数据
        items = []  # 实际数据
        total_items = 0  # 实际总数

        pagination = {
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": (total_items + page_size - 1) // page_size,
            "has_next": page < (total_items + page_size - 1) // page_size,
            "has_previous": page > 1,
        }

        paginated_data = PaginatedResponse(items=items, pagination=pagination)

        return ApiResponse(success=True, data=paginated_data, message="检查列表获取成功")

    except Exception as e:
        logger.error(f"获取检查列表异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DOC_SER_001",
                "type": "SERVICE_ERROR",
                "message": "获取检查列表服务暂时不可用",
            },
        )


@router.delete(
    "/checks/{check_id}",
    response_model=ApiResponse[bool],
    summary="取消检查任务",
    description="取消指定的检查任务（仅限排队中或运行中的任务）",
)
@monitor_endpoint("docgate_cancel_check")
async def cancel_check(
    check_id: str,
    current_user: User = Depends(get_current_active_user),
    client_info: Dict[str, Any] = Depends(get_client_info),
    docgate_service: DocGateService = Depends(get_docgate_service),
    _: bool = Depends(require_permissions(["docgate:write"])),
) -> ApiResponse[bool]:
    """
    ## 取消检查任务

    取消指定的文档质量检查任务。

    ### 取消条件
    - 任务状态为 `queued` 或 `running`
    - 任务属于当前用户
    - 用户有相应权限

    ### 注意事项
    - 已完成或失败的任务无法取消
    - 取消操作无法撤销
    - 已消耗的处理资源不会退还
    """
    try:
        result = await docgate_service.cancel_check(
            check_id=check_id, user_id=str(current_user.id)
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "DOC_CON_001",
                    "type": "CONFLICT_ERROR",
                    "message": "任务无法取消（可能已完成或不存在）",
                },
            )

        # 记录安全事件
        SecurityEvent.log_security_event(
            event_type="docgate_check_cancelled",
            user_id=str(current_user.id),
            ip_address=client_info["ip_address"],
            details={"check_id": check_id},
        )

        logger.info(f"用户 {current_user.id} 取消检查任务: {check_id}")

        return ApiResponse(
            success=True,
            data=True,
            message="检查任务已取消",
            request_id=client_info.get("request_id"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消检查任务异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DOC_SER_001",
                "type": "SERVICE_ERROR",
                "message": "取消检查任务服务暂时不可用",
            },
        )


# =============== 质量报告接口 ===============


@router.get(
    "/checks/{check_id}/report",
    response_model=ApiResponse[QualityReport],
    summary="获取详细报告",
    description="获取指定检查任务的详细质量报告",
)
@monitor_endpoint("docgate_get_report")
async def get_quality_report(
    check_id: str,
    format: str = Query("json", description="报告格式"),
    current_user: User = Depends(get_current_active_user),
    docgate_service: DocGateService = Depends(get_docgate_service),
    _: bool = Depends(require_permissions(["docgate:read"])),
) -> Union[ApiResponse[QualityReport], FileResponse, StreamingResponse]:
    """
    ## 获取详细质量报告

    获取指定检查任务的完整质量报告，包括：
    - 文档基本信息和统计
    - 质量评分和等级
    - 详细问题列表和修改建议
    - 可读性和结构指标
    - 链接和引用分析
    - 改进建议

    ### 支持格式
    - **json**: JSON格式（默认，API响应）
    - **html**: HTML格式（网页查看）
    - **pdf**: PDF格式（下载保存）

    ### 报告内容
    - **摘要**: 总体质量评分、问题数量统计
    - **问题列表**: 按严重程度分类的详细问题
    - **修改建议**: 针对每个问题的具体建议
    - **质量指标**: 可读性、结构、链接等指标
    - **改进建议**: 整体文档改进方向
    """
    try:
        pass  # Auto-fixed empty block
        # 获取报告数据
        report = await docgate_service.get_report(
            check_id=check_id, user_id=str(current_user.id)
        )

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "DOC_NOT_002",
                    "type": "NOT_FOUND",
                    "message": "检查任务或报告不存在",
                },
            )

        # 根据格式返回不同响应
        if format.lower() == "json":
            return ApiResponse(success=True, data=report, message="质量报告获取成功")
        elif format.lower() == "html":
            pass  # Auto-fixed empty block
            # 生成HTML报告
            html_content = await generate_html_report(report)
            return StreamingResponse(
                io.BytesIO(html_content.encode()),
                media_type="text/html",
                headers={
                    "Content-Disposition": f"inline; filename=report_{check_id}.html"
                },
            )
        elif format.lower() == "pdf":
            pass  # Auto-fixed empty block
            # 生成PDF报告
            pdf_path = await generate_pdf_report(report)
            return FileResponse(
                pdf_path,
                media_type="application/pdf",
                filename=f"report_{check_id}.pdf",
            )
        else:
            raise ValueError("不支持的报告格式")

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "DOC_VAL_002",
                "type": "VALIDATION_ERROR",
                "message": str(e),
            },
        )
    except Exception as e:
        logger.error(f"获取质量报告异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DOC_SER_003",
                "type": "SERVICE_ERROR",
                "message": "报告生成服务暂时不可用",
            },
        )


@router.get(
    "/checks/{check_id}/report/download",
    summary="下载报告文件",
    description="下载指定格式的报告文件",
)
@monitor_endpoint("docgate_download_report")
async def download_report(
    check_id: str,
    format: str = Query("pdf", description="下载格式"),
    current_user: User = Depends(get_current_active_user),
    docgate_service: DocGateService = Depends(get_docgate_service),
    _: bool = Depends(require_permissions(["docgate:read"])),
) -> FileResponse:
    """
    ## 下载报告文件

    下载指定格式的质量报告文件。

    ### 支持格式
    - **pdf**: PDF文件（推荐）
    - **html**: HTML文件
    - **json**: JSON文件

    ### 文件命名
    - PDF: `quality_report_{check_id}_{timestamp}.pdf`
    - HTML: `quality_report_{check_id}_{timestamp}.html`
    - JSON: `quality_report_{check_id}_{timestamp}.json`
    """
    try:
        pass  # Auto-fixed empty block
        # 获取报告
        report = await docgate_service.get_report(
            check_id=check_id, user_id=str(current_user.id)
        )

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "DOC_NOT_002",
                    "type": "NOT_FOUND",
                    "message": "检查任务或报告不存在",
                },
            )

        # 生成文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format.lower() == "pdf":
            file_path = await generate_pdf_report(report)
            filename = f"quality_report_{check_id}_{timestamp}.pdf"
            media_type = "application/pdf"
        elif format.lower() == "html":
            file_path = await generate_html_report_file(report)
            filename = f"quality_report_{check_id}_{timestamp}.html"
            media_type = "text/html"
        elif format.lower() == "json":
            file_path = await generate_json_report_file(report)
            filename = f"quality_report_{check_id}_{timestamp}.json"
            media_type = "application/json"
        else:
            raise ValueError("不支持的下载格式")

        return FileResponse(
            file_path,
            media_type=media_type,
            filename=filename,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "DOC_VAL_002",
                "type": "VALIDATION_ERROR",
                "message": str(e),
            },
        )
    except Exception as e:
        logger.error(f"下载报告异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DOC_SER_003",
                "type": "SERVICE_ERROR",
                "message": "报告下载服务暂时不可用",
            },
        )


# =============== 配置管理接口 ===============


@router.get(
    "/configs",
    response_model=ApiResponse[List[ConfigResponse]],
    summary="获取检查配置列表",
    description="获取用户可用的质量检查配置列表",
)
@monitor_endpoint("docgate_list_configs")
async def list_configs(
    current_user: User = Depends(get_current_active_user),
    config_service: ConfigService = Depends(get_config_service),
    _: bool = Depends(require_permissions(["docgate:read"])),
) -> ApiResponse[List[ConfigResponse]]:
    """
    ## 获取检查配置列表

    获取用户可用的所有质量检查配置，包括：
    - 系统预定义配置
    - 用户自定义配置
    - 公开共享配置

    ### 配置类型
    - **系统配置**: 由系统提供的标准配置
    - **用户配置**: 用户创建的私有配置
    - **公开配置**: 其他用户共享的配置

    ### 配置信息
    - 配置名称和描述
    - 检查规则详情
    - 使用统计
    - 创建和更新时间
    """
    try:
        configs = await config_service.get_configs(str(current_user.id))

        return ApiResponse(success=True, data=configs, message="配置列表获取成功")

    except Exception as e:
        logger.error(f"获取配置列表异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DOC_SER_001",
                "type": "SERVICE_ERROR",
                "message": "获取配置列表服务暂时不可用",
            },
        )


@router.post(
    "/configs",
    response_model=ApiResponse[ConfigResponse],
    status_code=status.HTTP_201_CREATED,
    summary="创建检查配置",
    description="创建新的质量检查配置",
)
@monitor_endpoint("docgate_create_config")
async def create_config(
    request: ConfigCreateRequest,
    current_user: User = Depends(get_current_active_user),
    client_info: Dict[str, Any] = Depends(get_client_info),
    config_service: ConfigService = Depends(get_config_service),
    _: bool = Depends(require_permissions(["docgate:config"])),
) -> ApiResponse[ConfigResponse]:
    """
    ## 创建检查配置

    创建新的质量检查配置，支持基于现有配置进行定制。

    ### 配置选项
    - **基础检查**: 语法、拼写、样式等
    - **高级检查**: 结构、链接、图片等
    - **自定义规则**: 用户定义的特殊检查规则
    - **共享设置**: 是否公开供其他用户使用

    ### 自定义规则
    支持基于正则表达式的自定义检查规则：
    - 术语一致性检查
    - 品牌词汇规范
    - 格式标准验证
    - 内容政策检查
    """
    try:
        result = await config_service.create_config(
            user_id=str(current_user.id), request=request
        )

        # 记录安全事件
        SecurityEvent.log_security_event(
            event_type="docgate_config_created",
            user_id=str(current_user.id),
            ip_address=client_info["ip_address"],
            details={
                "config_name": request.name,
                "is_public": request.is_public,
            },
        )

        logger.info(f"用户 {current_user.id} 创建配置: {request.name}")

        return ApiResponse(
            success=True,
            data=result,
            message="配置创建成功",
            request_id=client_info.get("request_id"),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "DOC_VAL_002",
                "type": "VALIDATION_ERROR",
                "message": str(e),
            },
        )
    except Exception as e:
        logger.error(f"创建配置异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DOC_SER_001",
                "type": "SERVICE_ERROR",
                "message": "创建配置服务暂时不可用",
            },
        )


# =============== Webhook管理接口 ===============


@router.post(
    "/webhooks",
    response_model=ApiResponse[WebhookResponse],
    status_code=status.HTTP_201_CREATED,
    summary="创建Webhook配置",
    description="创建新的Webhook事件通知配置",
)
@monitor_endpoint("docgate_create_webhook")
async def create_webhook(
    request: WebhookCreateRequest,
    current_user: User = Depends(get_current_active_user),
    client_info: Dict[str, Any] = Depends(get_client_info),
    webhook_service: WebhookService = Depends(get_webhook_service),
    _: bool = Depends(require_permissions(["docgate:webhook"])),
) -> ApiResponse[WebhookResponse]:
    """
    ## 创建Webhook配置

    创建新的Webhook事件通知配置，实现质量检查事件的自动通知。

    ### 支持事件
    - **check.started**: 检查任务开始
    - **check.completed**: 检查任务完成
    - **check.failed**: 检查任务失败
    - **report.generated**: 报告生成完成

    ### 过滤条件
    - **文档模式**: 支持glob模式匹配
    - **严重程度**: 只推送特定严重程度以上的问题
    - **状态过滤**: 只推送特定状态的任务

    ### 安全特性
    - **HMAC签名**: 使用共享密钥签名验证
    - **重试机制**: 失败自动重试，最多10次
    - **超时控制**: 可配置请求超时时间
    """
    try:
        result = await webhook_service.create_webhook(
            user_id=str(current_user.id), request=request
        )

        # 记录安全事件
        SecurityEvent.log_security_event(
            event_type="docgate_webhook_created",
            user_id=str(current_user.id),
            ip_address=client_info["ip_address"],
            details={
                "webhook_name": request.name,
                "webhook_url": str(request.url),
                "events": [event.value for event in request.events],
            },
        )

        logger.info(f"用户 {current_user.id} 创建Webhook: {request.name}")

        return ApiResponse(
            success=True,
            data=result,
            message="Webhook配置创建成功",
            request_id=client_info.get("request_id"),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "DOC_VAL_002",
                "type": "VALIDATION_ERROR",
                "message": str(e),
            },
        )
    except Exception as e:
        logger.error(f"创建Webhook异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DOC_SER_001",
                "type": "SERVICE_ERROR",
                "message": "创建Webhook服务暂时不可用",
            },
        )


@router.get(
    "/webhooks",
    response_model=ApiResponse[List[WebhookResponse]],
    summary="获取Webhook列表",
    description="获取用户的Webhook配置列表",
)
@monitor_endpoint("docgate_list_webhooks")
async def list_webhooks(
    current_user: User = Depends(get_current_active_user),
    webhook_service: WebhookService = Depends(get_webhook_service),
    _: bool = Depends(require_permissions(["docgate:webhook"])),
) -> ApiResponse[List[WebhookResponse]]:
    """
    ## 获取Webhook列表

    获取用户创建的所有Webhook配置，包括：
    - 基本配置信息
    - 订阅事件列表
    - 触发统计
    - 状态信息
    """
    try:
        webhooks = await webhook_service.get_webhooks(str(current_user.id))

        return ApiResponse(success=True, data=webhooks, message="Webhook列表获取成功")

    except Exception as e:
        logger.error(f"获取Webhook列表异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DOC_SER_001",
                "type": "SERVICE_ERROR",
                "message": "获取Webhook列表服务暂时不可用",
            },
        )


@router.post(
    "/webhooks/{webhook_id}/test",
    response_model=ApiResponse[bool],
    summary="测试Webhook",
    description="发送测试事件到指定Webhook",
)
@monitor_endpoint("docgate_test_webhook")
async def test_webhook(
    webhook_id: str,
    current_user: User = Depends(get_current_active_user),
    client_info: Dict[str, Any] = Depends(get_client_info),
    webhook_service: WebhookService = Depends(get_webhook_service),
    _: bool = Depends(require_permissions(["docgate:webhook"])),
) -> ApiResponse[bool]:
    """
    ## 测试Webhook

    发送测试事件到指定的Webhook URL，验证配置是否正确。

    ### 测试内容
    - 发送模拟的检查完成事件
    - 验证URL可访问性
    - 检查响应状态码
    - 验证HMAC签名（如果配置）

    ### 测试结果
    - 成功：返回true，记录成功日志
    - 失败：返回false，记录失败原因
    """
    try:
        result = await webhook_service.test_webhook(
            webhook_id=webhook_id, user_id=str(current_user.id)
        )

        # 记录测试事件
        SecurityEvent.log_security_event(
            event_type="docgate_webhook_tested",
            user_id=str(current_user.id),
            ip_address=client_info["ip_address"],
            details={
                "webhook_id": webhook_id,
                "test_result": result,
            },
        )

        message = "Webhook测试成功" if result else "Webhook测试失败"
        logger.info(f"用户 {current_user.id} 测试Webhook {webhook_id}: {result}")

        return ApiResponse(
            success=True,
            data=result,
            message=message,
            request_id=client_info.get("request_id"),
        )

    except Exception as e:
        logger.error(f"测试Webhook异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DOC_SER_001",
                "type": "SERVICE_ERROR",
                "message": "测试Webhook服务暂时不可用",
            },
        )


# =============== 系统管理接口 ===============


@router.get(
    "/health",
    response_model=ApiResponse[SystemHealth],
    summary="获取系统状态",
    description="获取DocGate系统的健康状态和运行指标",
)
@monitor_endpoint("docgate_health_check")
async def get_system_health(
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permissions(["docgate:read"])),
) -> ApiResponse[SystemHealth]:
    """
    ## 获取系统状态

    获取DocGate系统的实时健康状态和运行指标。

    ### 监控项目
    - **系统状态**: 整体健康状况
    - **服务状态**: 各子服务运行状态
    - **性能指标**: 处理时间、成功率等
    - **资源使用**: 队列长度、并发数等

    ### 状态说明
    - **healthy**: 系统运行正常
    - **degraded**: 部分功能受影响
    - **unhealthy**: 系统故障
    """
    try:
        pass  # Auto-fixed empty block
        # 实际实现中应该检查各个服务的状态
        health_data = SystemHealth(
            status="healthy",
            version="1.0.0",
            uptime=86400,  # 示例数据
            services={
                "document_parser": "healthy",
                "quality_checker": "healthy",
                "report_generator": "healthy",
                "webhook_service": "healthy",
            },
            metrics={
                "checks_today": 1250,
                "avg_processing_time": 45.2,
                "success_rate": 98.5,
                "queue_length": 12,
                "active_checks": 5,
            },
            timestamp=datetime.utcnow(),
        )

        return ApiResponse(success=True, data=health_data, message="系统状态获取成功")

    except Exception as e:
        logger.error(f"获取系统状态异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DOC_SER_001",
                "type": "SERVICE_ERROR",
                "message": "获取系统状态服务暂时不可用",
            },
        )


@router.get(
    "/stats",
    response_model=ApiResponse[UsageStats],
    summary="获取使用统计",
    description="获取文档质量检查的使用统计数据",
)
@monitor_endpoint("docgate_get_stats")
async def get_usage_stats(
    period: str = Query("day", description="统计周期"),
    from_date: Optional[datetime] = Query(None, alias="from", description="开始日期"),
    to_date: Optional[datetime] = Query(None, alias="to", description="结束日期"),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_permissions(["docgate:read"])),
) -> ApiResponse[UsageStats]:
    """
    ## 获取使用统计

    获取指定时间段内的文档质量检查使用统计。

    ### 统计周期
    - **day**: 按天统计
    - **week**: 按周统计
    - **month**: 按月统计

    ### 统计内容
    - 检查任务数量和状态分布
    - 平均处理时间
    - 文档类型分布
    - 最常见问题类型
    - 质量评分趋势

    ### 时间范围
    - 默认返回最近7天的数据
    - 可通过from/to参数自定义范围
    - 最长支持1年的历史数据
    """
    try:
        pass  # Auto-fixed empty block
        # 设置默认时间范围
        if not to_date:
            to_date = datetime.utcnow()
        if not from_date:
            if period == "day":
                from_date = to_date - timedelta(days=7)
            elif period == "week":
                from_date = to_date - timedelta(weeks=4)
            elif period == "month":
                from_date = to_date - timedelta(days=90)
            else:
                from_date = to_date - timedelta(days=7)

        # 实际实现中应该从数据库查询统计数据
        stats_data = UsageStats(
            period=period,
            start_date=from_date,
            end_date=to_date,
            total_checks=150,
            completed_checks=145,
            failed_checks=5,
            avg_processing_time=45.2,
            total_documents=145,
            total_issues_found=1250,
            most_common_issues=[
                {"type": "spelling", "count": 350},
                {"type": "grammar", "count": 280},
                {"type": "style", "count": 220},
            ],
            document_types={
                "markdown": 120,
                "html": 25,
            },
        )

        return ApiResponse(success=True, data=stats_data, message="使用统计获取成功")

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "DOC_VAL_002",
                "type": "VALIDATION_ERROR",
                "message": str(e),
            },
        )
    except Exception as e:
        logger.error(f"获取使用统计异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DOC_SER_001",
                "type": "SERVICE_ERROR",
                "message": "获取使用统计服务暂时不可用",
            },
        )


# =============== 辅助函数 ===============


async def generate_html_report(report: QualityReport) -> str:
    """生成HTML格式报告"""
    # 实际实现中应该使用模板引擎生成HTML
    return f"<html><body><h1>Quality Report for {report.document_info.name}</h1></body></html>"


async def generate_pdf_report(report: QualityReport) -> str:
    """生成PDF格式报告"""
    # 实际实现中应该使用PDF生成库
    # 返回临时文件路径
    import tempfile

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_file.close()
    return temp_file.name


async def generate_html_report_file(report: QualityReport) -> str:
    """生成HTML报告文件"""
    import tempfile

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w")
    html_content = await generate_html_report(report)
    temp_file.write(html_content)
    temp_file.close()
    return temp_file.name


async def generate_json_report_file(report: QualityReport) -> str:
    """生成JSON报告文件"""
    import tempfile
    import json

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w")
    json.dump(report.dict(), temp_file, indent=2, default=str)
    temp_file.close()
    return temp_file.name
