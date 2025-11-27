"""
认证相关的数据模型
"""

from loguru import logger
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求模型"""

    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, max_length=100, description="密码")


class LoginResponse(BaseModel):
    """登录响应模型"""

    success: bool = Field(..., description="是否登录成功")
    message: str = Field(..., description="响应消息")
    token: str | None = Field(None, description="访问令牌")


class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""

    current_password: str = Field(
        ..., min_length=1, max_length=100, description="当前密码"
    )
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")
    confirm_password: str = Field(
        ..., min_length=6, max_length=100, description="确认新密码"
    )

    def validate_passwords_match(self) -> bool:
        """验证两次输入的新密码是否一致"""
        return self.new_password == self.confirm_password


class ChangePasswordResponse(BaseModel):
    """修改密码响应模型"""

    success: bool = Field(..., description="是否修改成功")
    message: str = Field(..., description="响应消息")


class AuthVerifyResponse(BaseModel):
    """认证验证响应模型"""

    success: bool = Field(..., description="认证是否有效")
    message: str = Field(..., description="响应消息")
    username: str = Field(..., description="当前登录用户名")


class LogoutResponse(BaseModel):
    """退出登录响应模型"""

    success: bool = Field(..., description="是否退出成功")
    message: str = Field(..., description="响应消息")


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 添加项目根目录到 Python 路径
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    logger.info("🔐 认证数据模型")
    logger.info("定义用户认证相关的 Pydantic 数据模型")
    logger.info("- LoginRequest - 登录请求模型")
    logger.info("- LoginResponse - 登录响应模型")
    logger.info("- TokenValidationResponse - 令牌验证响应模型")
    logger.info("- LogoutResponse - 退出登录响应模型")
