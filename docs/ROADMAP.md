# 路线图

> **Version**: v5.3.3
> **Status**: v5.3 UI 体验阶段

## 已完成

| 版本 | 内容 | 状态 |
|------|------|------|
| v5.2.3 | Architecture Stabilization Release（架构冻结 + 发布） | ✅ |
| v5.3.0 | Project Cleanup（CHANGELOG / badge / PR 模板 / docs 瘦身） | ✅ |
| v5.3.1 | Runtime Fix（history.db 路径统一 + netifaces 替换） | ✅ |
| v5.3.2 | Dashboard 2.0（System Overview + 状态卡片） | ✅ |
| v5.3.3 | History UX（时间快捷键 + 多曲线 + tooltip + Summary） | ✅ |

## 进行中

| 项 | 内容 |
|----|------|
| v5.3.4 | Device View（设备列表 + 在线状态 + IP + 最后通信时间） |

## 待完成

| Phase | 内容 | 优先级 |
|-------|------|--------|
| v5.3.5 | Alert 体验（生命周期 / 恢复检测） | P2 |
| 5-5C | Retention Settings 集成 | P2 |
| v5.4 | 新功能（告警通知 / 远程控制 / 自动发现增强） | P2 |
| Phase 6 | 高级告警引擎（多级告警 / 规则引擎） | P3 |

## 暂缓（不做）

- ❌ Qt6 / Electron 迁移
- ❌ 云端同步
- ❌ 插件系统
- ❌ 多用户权限
- ❌ Storage schema v2

## 节奏原则

1. 不再频繁建 tag，有明显体验变化再打版本
2. 小改动直接 commit，不走完整 Release 流程
3. 优先"用户能看到的"，其次工程质量

## 测试

- 框架：自定义 check runner（非 pytest）
- 最新全量回归：**989/989 PASS**
- 基线明细见 `docs/releases/baseline_v5.2.3.txt`
