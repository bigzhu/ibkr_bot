"""
用户认证和系统配置相关的数据模型

定义管理员认证和系统配置的Pydantic模型
"""

from datetime import datetime

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, field_validator


class AdminAuth(BaseModel):
    """管理员认证模型"""

    id: int | None = None
    username: str = Field(..., description="用户名")
    password_hash: str = Field(..., description="密码哈希")
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名格式"""
        if not v or len(v) < 3:
            raise ValueError("用户名长度至少3个字符")
        return v

    model_config = ConfigDict(use_enum_values=True)


class SystemConfig(BaseModel):
    """系统配置模型"""

    id: int | None = None
    config_key: str = Field(..., description="配置键")
    config_value: str | None = Field(default=None, description="配置值")
    config_type: str = Field(..., description="配置类型")
    description: str | None = Field(default=None, description="配置描述")
    is_encrypted: bool = Field(..., description="是否加密")
    is_required: bool = Field(..., description="是否必需")
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("config_key")
    @classmethod
    def validate_key(cls, v: str) -> str:
        """验证配置键格式"""
        if not v or not v.replace("_", "").replace(".", "").isalnum():
            raise ValueError("配置键只能包含字母,数字,下划线和点")
        return v

    model_config = ConfigDict(use_enum_values=True)


if __name__ == "__main__":
    """认证和配置模型测试"""
    logger.info("🔐 用户认证和系统配置模型")
    logger.info("定义管理员认证和系统配置的数据模型:")
    logger.info("- AdminAuth: 管理员认证模型")
    logger.info("- SystemConfig: 系统配置模型")

    # 测试模型创建
    admin = AdminAuth(username="admin", password_hash="hash123")
    config = SystemConfig(
        config_key="test.key",
        config_value="test_value",
        config_type="string",
        is_encrypted=False,
        is_required=False,
    )
    logger.info(
        f"\n测试模型: AdminAuth({admin.username}), SystemConfig({config.config_key})"
    )
