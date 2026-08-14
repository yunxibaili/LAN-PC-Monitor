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

from host.storage.database import Database
from host.storage.repositories.metrics_repo import MetricsRepository
from host.storage.repositories.alerts_repo import AlertsRepository
from host.storage.repositories.sessions_repo import SessionsRepository
from host.facade.history_facade import HistoryFacade
from host.storage.retention import RetentionPolicy, RetentionService

log = logging.getLogger("host.service.storage")


class StorageService:
    """统一管理 SQLite 连接 + Repository 组装。"""

    def __init__(self, db_path: str = "history.db"):
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
