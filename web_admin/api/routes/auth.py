"""
认证相关的 API 路由
"""

from datetime import UTC, datetime, timedelta
from typing import Any, cast

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger

from shared.config import Config

from ..utils.auth_manager import get_auth_manager

# Work around incomplete typing of PyJWT in strict mode
jwt_encode = cast(Any, jwt.encode)  # type: ignore[reportUnknownMemberType]
jwt_decode = cast(Any, jwt.decode)  # type: ignore[reportUnknownMemberType]

# 使用Web Admin专用的认证管理器
auth_manager = get_auth_manager()
from ..models.auth import (
    AuthVerifyResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
)

# 创建路由器
router = APIRouter(tags=["认证"])

# JWT 配置
SECRET_KEY = Config.get_admin_jwt_secret()  # 从环境变量读取,开发环境有默认值
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 20160  # 14天

# HTTP Bearer 认证
security = HTTPBearer()


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    """创建 JWT 访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = str(jwt_encode(to_encode, SECRET_KEY, algorithm=ALGORITHM))
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials) -> str:
    """验证 JWT 令牌"""
    payload = cast(
        dict[str, Any],
        jwt_decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]),
    )
    username_val = payload.get("sub")
    if username_val is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return str(username_val)


# FastAPI依赖注入 - 简化认证流程
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """获取当前用户 - FastAPI依赖注入"""
    return verify_token(credentials)


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    """
    管理员登录

    - **username**: 用户名
    - **password**: 密码
    """
    # 验证用户名和密码
    if auth_manager.authenticate_admin(request.username, request.password):
        # 创建访问令牌
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": request.username}, expires_delta=access_token_expires
        )

        return LoginResponse(success=True, message="登录成功", token=access_token)
    else:
        return LoginResponse(success=False, message="用户名或密码错误", token=None)


@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(
    request: ChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> ChangePasswordResponse:
    """
    修改管理员密码

    需要提供当前密码和新密码
    """
    # 验证两次输入的新密码是否一致
    if not request.validate_passwords_match():
        return ChangePasswordResponse(success=False, message="两次输入的新密码不一致")

    # 验证当前密码
    current_user = verify_token(credentials)
    if not auth_manager.authenticate_admin(current_user, request.current_password):
        return ChangePasswordResponse(success=False, message="当前密码错误")

    # 更新密码
    if auth_manager.update_admin_password(current_user, request.new_password):
        return ChangePasswordResponse(
            success=True, message="密码修改成功,请使用新密码重新登录"
        )
    else:
        return ChangePasswordResponse(success=False, message="密码修改失败")


@router.get("/verify", response_model=AuthVerifyResponse)
async def verify_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AuthVerifyResponse:
    """
    验证当前登录状态

    返回当前登录的用户信息
    """
    current_user = verify_token(credentials)
    return AuthVerifyResponse(success=True, message="认证有效", username=current_user)


@router.post("/logout", response_model=LogoutResponse)
async def logout() -> LogoutResponse:
    """
    退出登录

    由于使用 JWT,实际的登出需要在前端删除 token
    """
    return LogoutResponse(success=True, message="退出登录成功")


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 添加项目根目录到 Python 路径
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    logger.info("🔐 认证路由模块")
    logger.info("提供用户认证相关的 API 端点")
    logger.info("- POST /api/v1/login - 用户登录")
    logger.info("- POST /api/v1/logout - 用户退出登录")
