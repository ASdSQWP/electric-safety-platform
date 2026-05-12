"""应用配置"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "电力作业AI安全监管平台"
    debug: bool = True

    # 数据库
    database_url: str = "postgresql+asyncpg://esafety:esafety123@localhost:5432/esafety"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_bucket: str = "esafety"

    # 模型路径
    model_dir: str = "./models/weights"
    yolo_model: str = "yolov8n.pt"

    # LLM
    llm_api_base: str = "https://api.deepseek.com/v1"
    llm_api_key: str = ""
    llm_model: str = "deepseek-chat"

    # 知识库
    chroma_db_dir: str = "./chroma_db"
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"

    # 报告
    report_dir: str = "./reports"

    class Config:
        env_file = ".env"


settings = Settings()
