@echo off
chcp 65001 >nul
title 副机端（Client · 本机仪表盘 + 节点管理）菜单
:menu
cls
echo ============================================
echo        副机端（Client · 本机仪表盘 + 节点管理）
echo        本机数据 + 已接入节点摘要
echo ============================================
echo  1. 启动副机端
echo  2. 安装开机自启动（注册表，无需管理员）
echo  3. 卸载开机自启动
echo  0. 退出
echo ============================================
set /p choice=请选择:

if "%choice%"=="1" (
    python -m client
    goto end
)
if "%choice%"=="2" (
    python -m client --install-startup
    goto end
)
if "%choice%"=="3" (
    python -m client --remove-startup
    goto end
)
if "%choice%"=="0" exit
echo 无效选择，请重新输入。
:end
pause
goto menu
