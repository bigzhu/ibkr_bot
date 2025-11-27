"""
认证 API 基础测试: 登录与验证
"""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from web_admin.api.app import app


def test_login_and_verify():
    client = TestClient(app)

    # 使用默认管理账号登录(见 WebAdminAuthManager)
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "z129854"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("success") is True
    token = body.get("token")
    assert isinstance(token, str) and len(token) > 10

    # 携带 token 调用 verify
    resp2 = client.get(
        "/api/v1/auth/verify",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2.get("success") is True
    assert data2.get("username") == "admin"
