# -*- coding: utf-8 -*-
"""
Retention —— 数据保留策略与清理服务（v5.2 Phase 5-5A）。

职责：
  - RetentionPolicy：保留天数配置
  - RetentionService：调用 Repository.delete_before() 清理过期数据

不负责：
  - 定时触发（5-5B）
  - UI 设置（5-5C）
  - VACUUM / archive / compression
"""
import logging
import time
from dataclasses import dataclass

from host.storage.repositories.metrics_repo import MetricsRepository
from host.storage.repositories.alerts_repo import AlertsRepository
from host.storage.repositories.sessions_repo import SessionsRepository

log = logging.getLogger("host.storage.retention")


@dataclass
class RetentionPolicy:
    """数据保留策略（天）。"""
    metrics_days: int = 30
    alerts_days: int = 90
    sessions_days: int = 90

    def cutoff(self, days: int, now: float = None) -> float:
        """返回删除阈值（Unix 时间戳），timestamp < cutoff 将被删除。"""
        if now is None:
            now = time.time()
        return now - days * 86400


class RetentionService:
    """清理服务：删除过期数据，返回各表删除数量。"""

    def __init__(self, policy: RetentionPolicy,
                 metrics_repo: MetricsRepository,
                 alerts_repo: AlertsRepository,
                 sessions_repo: SessionsRepository):
        self._policy = policy
        self._metrics_repo = metrics_repo
        self._alerts_repo = alerts_repo
        self._sessions_repo = sessions_repo

    def run(self, now: float = None) -> dict:
        """执行清理。返回 {metrics, alerts, sessions} 删除数量。"""
        result = {
            "metrics": self._metrics_repo.delete_before(
                self._policy.cutoff(self._policy.metrics_days, now)),
            "alerts": self._alerts_repo.delete_before(
                self._policy.cutoff(self._policy.alerts_days, now)),
            "sessions": self._sessions_repo.delete_before(
                self._policy.cutoff(self._policy.sessions_days, now)),
        }
        log.info("Retention cleanup: %s", result)
        return result
