# -*- coding: utf-8 -*-
"""ThemeIcons —— SVG 图标常量（v5.4 Gentelella 对齐）。

基于 Gentelella v4 shell-render.js ICONS 提取。
18x18 viewBox，stroke="currentColor"，stroke-width=1.5。
"""


class ThemeIcons:
    """SVG 图标（导航用）。"""

    # 导航图标（Gentelella SVG）
    DASHBOARD = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="4" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="10" width="7" height="11" rx="1.5"/></svg>'
    DEVICES = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="8" r="4"/><path d="M5 20c0-3.9 3.1-7 7-7s7 3.1 7 7"/></svg>'
    MONITOR = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 19V5M8 19v-8M12 19V9M16 19v-5M20 19v-9"/></svg>'
    ALERTS = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 3a6 6 0 00-6 6c0 6-3 7-3 7h18s-3-1-3-7a6 6 0 00-6-6z"/><path d="M10.5 21a1.5 1.5 0 003 0"/></svg>'
    HISTORY = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M8 4v6M16 4v6"/></svg>'
    SETTINGS = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M5.6 18.4l2.1-2.1M16.3 7.7l2.1-2.1"/></svg>'

    # 状态
    ONLINE = "●"
    OFFLINE = "○"
    RECONNECTING = "◐"

    # 操作
    ADD = "+"
    SCAN = "🔍"
    CONNECT_CODE = "🔗"
    CLIPBOARD = "📋"
    IMPORT = "📂"
    EXPORT = "💾"
    BACK = "←"
    CLOSE = "×"
    SETTINGS_GEAR = "⚙"

    # 网络
    UPLOAD = "↑"
    DOWNLOAD = "↓"
    CONNECTED = "●"
