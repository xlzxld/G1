"""统一安全配置 — 安全项无默认值，缺失即启动失败（fail-fast）。

来源：8/6 审查报告 P0-3（SECRET_KEY / DATABASE_URL 硬编码兜底）与 P1-5（CORS 兜底为 *）。
所有模块从这里导入，禁止在业务代码中直接 os.getenv 读取安全项。
"""
import os


def _require(name: str) -> str:
    val = os.getenv(name)
    if not val or not val.strip():
        raise RuntimeError(
            f"缺少必需环境变量 {name}：安全配置禁止默认值，服务拒绝启动。"
            f"请在 .env 或部署环境中设置后重试。"
        )
    return val.strip()


SECRET_KEY = _require("SECRET_KEY")
DATABASE_URL = _require("DATABASE_URL")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7   # access token：7 天（含 token_version 吊销）
REFRESH_TOKEN_EXPIRE_DAYS = 30              # refresh token：30 天

# CORS 白名单：逗号分隔；为空视为配置缺失（生产不允许退化为 *）
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

# 审计中间件开关（测试环境置 0 以隔离审计写入）
AUDIT_LOG_ENABLED = os.getenv("AUDIT_LOG_ENABLED", "1") != "0"
