# -*- coding: utf-8 -*-
"""
开机自启动管理（见《技术文档.md》§13）。

- 采集节点：schtasks 计划任务（需管理员，/RL HIGHEST 提权，pythonw.exe 静默）
- 监控主机：注册表 HKCU Run 项（无需管理员）
- 统一封装 install/remove，入口程序通过 --install-startup/--remove-startup 调用
"""
import logging
import os
import subprocess
import sys

log = logging.getLogger("common.startup")

# 任务/注册表名称
NODE_TASK_NAME = "PC_Monitor_Node"
CLIENT_RUN_NAME = "PC_Monitor_Client"
HOST_RUN_NAME = "PC_Monitor_Host"

# 注册表 Run 键路径
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _pythonw_path() -> str:
    """pythonw.exe 路径（无控制台窗口），不存在时回退 python.exe。"""
    exe = sys.executable
    alt = exe.replace("python.exe", "pythonw.exe")
    return alt if os.path.exists(alt) else exe


def install_node_startup() -> bool:
    """
    安装采集节点开机自启（schtasks /SC ONLOGON /RL HIGHEST，需管理员）。
    返回是否成功。
    """
    if sys.platform != "win32":
        log.warning("非 Windows 平台，跳过开机自启安装")
        return False
    exe = _pythonw_path()
    cmd = f'{exe} -m node'
    try:
        subprocess.run(
            ["schtasks", "/Create", "/TN", NODE_TASK_NAME,
             "/TR", f'"{cmd}"', "/SC", "ONLOGON",
             "/RL", "HIGHEST", "/F"],
            check=True, capture_output=True, text=True)
        log.info("采集节点开机自启已安装: %s", cmd)
        return True
    except subprocess.CalledProcessError as e:
        log.error("安装节点自启失败（可能需要管理员权限）: %s", e.stderr.strip())
        return False


def remove_node_startup() -> bool:
    """卸载采集节点开机自启。"""
    if sys.platform != "win32":
        return False
    try:
        subprocess.run(["schtasks", "/Delete", "/TN", NODE_TASK_NAME, "/F"],
                       check=True, capture_output=True, text=True)
        log.info("采集节点开机自启已卸载")
        return True
    except subprocess.CalledProcessError as e:
        log.error("卸载节点自启失败: %s", e.stderr.strip())
        return False


def install_client_startup() -> bool:
    """安装副机端开机自启（注册表 HKCU Run，无需管理员，§14.3）。"""
    if sys.platform != "win32":
        log.warning("非 Windows 平台，跳过开机自启安装")
        return False
    try:
        import winreg
        exe = _pythonw_path()
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                            winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, CLIENT_RUN_NAME, 0, winreg.REG_SZ,
                              f'{exe} -m client')
        log.info("副机端开机自启已安装")
        return True
    except Exception as e:
        log.error("安装副机端自启失败: %s", e)
        return False


def remove_client_startup() -> bool:
    """卸载副机端开机自启。"""
    if sys.platform != "win32":
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                            winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, CLIENT_RUN_NAME)
        log.info("副机端开机自启已卸载")
        return True
    except FileNotFoundError:
        log.info("副机端开机自启不存在")
        return True
    except Exception as e:
        log.error("卸载副机端自启失败: %s", e)
        return False


def install_host_startup() -> bool:
    """安装监控主机开机自启（注册表 HKCU Run，无需管理员）。"""
    if sys.platform != "win32":
        log.warning("非 Windows 平台，跳过开机自启安装")
        return False
    try:
        import winreg
        exe = _pythonw_path()
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                            winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, HOST_RUN_NAME, 0, winreg.REG_SZ,
                              f'{exe} -m host')
        log.info("监控主机开机自启已安装")
        return True
    except Exception as e:
        log.error("安装主机自启失败: %s", e)
        return False


def remove_host_startup() -> bool:
    """卸载监控主机开机自启。"""
    if sys.platform != "win32":
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                            winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, HOST_RUN_NAME)
        log.info("监控主机开机自启已卸载")
        return True
    except FileNotFoundError:
        log.info("监控主机开机自启不存在")
        return True
    except Exception as e:
        log.error("卸载主机自启失败: %s", e)
        return False
