"""Day61 HTTP 组合入口：API 使用的就是 CLI 已经验证过的正式应用。"""

from .api import create_app
from .bootstrap import build_application


def create_runtime_api():
    return create_app(build_application())
