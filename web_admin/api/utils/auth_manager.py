"""
Web Admin 认证管理器
专门用于Web Admin API的用户认证功能
"""

import hashlib
from pathlib import Path

from loguru import logger


class WebAdminAuthManager:
    """Web Admin 认证管理器"""

    def __init__(self) -> None:
        # 简化的认证实现 - 使用硬编码的管理员账户
        # 在生产环境中应该使用数据库存储
        self._admin_users = {
            "admin": {
                "password_hash": self._hash_password("z129854"),
                "username": "admin",
            }
        }

    def _hash_password(self, password: str) -> str:
        """对密码进行哈希处理"""
        # 使用简单的哈希方法,生产环境应使用bcrypt等更安全的方法
        salt = "binance_web_admin_salt"
        return hashlib.sha256((password + salt).encode()).hexdigest()

    def authenticate_admin(self, username: str, password: str) -> bool:
        """
        验证管理员用户名和密码

        Args:
            username: 用户名
            password: 密码

        Returns:
            bool: 验证是否成功
        """
        if username not in self._admin_users:
            return False

        user_data = self._admin_users[username]
        password_hash = self._hash_password(password)

        return user_data["password_hash"] == password_hash

    def update_admin_password(self, username: str, new_password: str) -> bool:
        """
        更新管理员密码

        Args:
            username: 用户名
            new_password: 新密码

        Returns:
            bool: 更新是否成功
        """
        if username not in self._admin_users:
            return False

        self._admin_users[username]["password_hash"] = self._hash_password(new_password)
        return True

    def get_admin_info(self, username: str) -> dict[str, str] | None:
        """
        获取管理员信息

        Args:
            username: 用户名

        Returns:
            dict: 用户信息,不包含密码
        """
        if username not in self._admin_users:
            return None

        user_data = self._admin_users[username].copy()
        # 移除密码哈希
        _ = user_data.pop("password_hash", None)
        return user_data


# 全局认证管理器实例
_auth_manager = None


def get_auth_manager() -> WebAdminAuthManager:
    """获取全局认证管理器实例"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = WebAdminAuthManager()
    return _auth_manager


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 添加项目根目录到 Python 路径
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    logger.info("🔐 Web Admin 认证管理器")
    logger.info("提供Web Admin API专用的用户认证功能")

    # 测试认证功能
    auth_manager = get_auth_manager()

    logger.info("\n🧪 测试认证功能:")
    logger.info(
        f"- admin/admin123: {auth_manager.authenticate_admin('admin', 'admin123')}"
    )
    logger.info(f"- admin/wrong: {auth_manager.authenticate_admin('admin', 'wrong')}")
    logger.info(
        f"- wrong/admin123: {auth_manager.authenticate_admin('wrong', 'admin123')}"
    )

    user_info = auth_manager.get_admin_info("admin")
    logger.info(f"- admin用户信息: {user_info}")
