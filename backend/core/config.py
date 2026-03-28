"""
核心配置类
从环境变量加载配置，使用 Pydantic Settings
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==================== 应用配置 ====================
    APP_NAME: str = "公文写作AI系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # 服务地址
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    # ==================== 数据库配置 ====================
    DATABASE_URL: str
    DATABASE_URL_SYNC: str

    # ==================== Redis 配置 ====================
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: str = ""

    # ==================== 文件存储配置 ====================
    STORAGE_ROOT: str = "./storage"
    UPLOAD_DIR: str = "./storage/uploads"
    THUMBNAIL_DIR: str = "./storage/thumbnails"
    CACHE_DIR: str = "./storage/cache"

    # 文件大小限制（转换为字节）
    MAX_FILE_SIZE_MB: int = 100
    MAX_IMAGE_SIZE_MB: int = 10

    @property
    def MAX_FILE_SIZE(self) -> int:
        """最大文件大小（字节）"""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def MAX_IMAGE_SIZE(self) -> int:
        """最大图片大小（字节）"""
        return self.MAX_IMAGE_SIZE_MB * 1024 * 1024

    # ==================== AI 服务配置 ====================
    # 硅基流动 DeepSeek
    SILICONFLOW_API_KEY: str = "sk-kshvajvqaupzrjoqxoclqtebvtafncsixxanhagknpsgggho"
    SILICONFLOW_BASE_URL: str = "https://api.siliconflow.cn/v1"
    DEEPSEEK_MODEL: str = "Pro/deepseek-ai/DeepSeek-V3"
    DEEPSEEK_R1_MODEL: str = "deepseek-ai/DeepSeek-R1"

    # OpenRouter (图片转译)
    OPENROUTER_API_KEY: str = "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"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_IMAGE_MODEL: str = "google/gemini-3-pro-image-preview"

    # ==================== 向量检索配置 ====================
    VECTOR_STORE_TYPE: str = "pgvector"  # pgvector 或 qdrant

    # Qdrant 配置（如果使用 Qdrant）
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "knowledge_base"

    # ==================== 任务队列配置 ====================
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ==================== 安全配置 ====================
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ==================== 简化认证配置 ====================
    DEFAULT_USER_ID: str = "00000000-0000-0000-0000-000000000001"  # 默认用户 ID（开发阶段）

    # ==================== CORS 配置 ====================
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    ALLOWED_METHODS: str = "*"
    ALLOWED_HEADERS: str = "*"

    @property
    def ALLOWED_ORIGINS_LIST(self) -> List[str]:
        """将 CORS 字符串转换为列表"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    # ==================== 日志配置 ====================
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"

    # ==================== Firecrawl 配置 ====================
    FIRECRAWL_API_KEY: str = "fc-35ad753d0ef8430e9109612903220c72"
    FIRECRAWL_BASE_URL: str = "https://api.firecrawl.dev"

    # ==================== 知识库配置 ====================
    KNOWLEDGE_RETRIEVAL_TOP_K: int = 5
    KNOWLEDGE_RERANK_ENABLED: bool = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()
