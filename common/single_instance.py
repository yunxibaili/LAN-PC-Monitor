# -*- coding: utf-8 -*-
"""
单实例检测 —— Windows 命名互斥体（见《README.md》§12.1）。

- 采集节点：name="Global\\PC_Monitor_Node"
- 监控主机：name="Global\\PC_Monitor_Host"
- mutex 对象必须保持引用（变量存活），否则被 GC 释放导致检测失效。
- 非 Windows 环境（开发调试）降级为锁文件方案。
"""
import logging
import os
import sys
import tempfile

log = logging.getLogger("common.single_instance")


def ensure_single_instance(name: str = "Global\\PC_Monitor_Node") -> object:
    """
    尝试获取命名互斥体；已有实例则返回 None。

    :param name: 互斥体名称（建议 Global\\ 前缀跨会话生效）
    :return: 互斥体对象（需保持引用）或锁文件句柄；已有实例返回 None
    """
    if sys.platform == "win32":
        try:
            import win32event
            import win32api
            import winerror
            mutex = win32event.CreateMutex(None, False, name)
            if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
                log.warning("已有实例运行（互斥体 %s）", name)
                return None
            return mutex  # 保持引用防止被 GC 释放
        except ImportError:
            log.debug("pywin32 不可用，降级锁文件方案")
        except Exception as e:
            log.warning("命名互斥体创建失败，降级锁文件方案: %s", e)

    # 非 Windows / pywin32 缺失：锁文件方案（开发调试用）
    lock_name = "".join(c for c in name if c.isalnum()) + ".lock"
    lock_path = os.path.join(tempfile.gettempdir(), lock_name)
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        # 返回 (fd, lock_path) 元组，释放时一并删除锁文件
        return (fd, lock_path)
    except FileExistsError:
        log.warning("已有实例运行（锁文件 %s）", lock_path)
        return None
    except OSError as e:
        log.warning("锁文件创建失败: %s", e)
        return None


def release_single_instance(handle) -> None:
    """释放单实例锁（程序退出时调用）。"""
    if handle is None:
        return
    if isinstance(handle, tuple):  # 锁文件方案：(fd, lock_path)
        fd, lock_path = handle
        try:
            os.close(fd)
        except Exception:
            pass
        try:
            os.remove(lock_path)
        except OSError:
            pass
    # win32 mutex 随进程退出自动释放，无需显式关闭
