"""
最小 API 健康检查测试

验证 FastAPI 应用可导入且基础路由可用.
"""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

# 确保项目根目录在导入路径中
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from web_admin.api.app import app


def test_root_route():
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("message")


def test_health_route():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "healthy"
