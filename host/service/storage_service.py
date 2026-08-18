# -*- coding: utf-8 -*-
"""
StorageService —— 存储层组装与生命周期管理（v5.2 Phase 5-5B）。

职责：
  - 创建 Database 连接 + 三个 Repository
  - 提供 HistoryFacade / RetentionService 组装
  - 管理连接关闭

不负责：
  - 业务查询（Repository 负责）
  - 清理策略（RetentionService 负责）
  - UI 数据转换
"""
import logging
import os

from host.storage.database import Database
from host.storage.repositories.metrics_repo import MetricsRepository
from host.storage.repositories.alerts_repo import AlertsRepository
from host.storage.repositories.sessions_repo import SessionsRepository
from host.facade.history_facade import HistoryFacade
from host.storage.retention import RetentionPolicy, RetentionService

log = logging.getLogger("host.service.storage")


def get_default_db_path() -> str:
    """
    返回用户数据目录下的数据库路径（v5.3.1 起，不再依赖进程 CWD）。

    Windows: %APPDATA%/LAN-PC-Monitor/data/history.db
    其它:    ~/.config/LAN-PC-Monitor/data/history.db
    目录不存在时自动创建。
    """
    base = os.environ.get("APPDATA") or os.path.join(
        os.path.expanduser("~"), ".config")
    data_dir = os.path.join(base, "LAN-PC-Monitor", "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "history.db")


class StorageService:
    """统一管理 SQLite 连接 + Repository 组装。"""

    def __init__(self, db_path: str = ""):
        """
        :param db_path: 数据库文件路径。空串/省略使用 get_default_db_path()
                        （用户数据目录，与启动方式无关）；":memory:" 为测试用。
        """
        if not db_path:
            db_path = get_default_db_path()
        self._db = Database(db_path)
        self._db.connect()
        self.metrics_repo = MetricsRepository(self._db)
        self.alerts_repo = AlertsRepository(self._db)
        self.sessions_repo = SessionsRepository(self._db)

    def history_facade(self) -> HistoryFacade:
        """返回历史读取门面。"""
        return HistoryFacade(self.metrics_repo)

    def retention_service(self, policy: RetentionPolicy = None) -> RetentionService:
        """返回数据保留清理服务。"""
        policy = policy or RetentionPolicy()
        return RetentionService(
            policy, self.metrics_repo, self.alerts_repo, self.sessions_repo)

    def run_retention(self, now: float = None) -> dict:
        """执行一次数据保留清理。"""
        return self.retention_service().run(now)

    def close(self) -> None:
        """关闭数据库连接。"""
        self._db.close()
