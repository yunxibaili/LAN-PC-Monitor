@echo off
chcp 65001 >nul
title 采集节点（Node · 无界面）菜单
:menu
cls
echo ============================================
echo        采集节点（Node · 无界面后台）
echo        被监控端，采集 + 推送
echo ============================================
echo  1. 启动节点（需管理员，后台运行）
echo  2. 安装开机自启动（需管理员）
echo  3. 卸载开机自启动
echo  0. 退出
echo ============================================
set /p choice=请选择:

if "%choice%"=="1" (
    python -m node
    goto end
)
if "%choice%"=="2" (
    python -m node --install-startup
    goto end
)
if "%choice%"=="3" (
    python -m node --remove-startup
    goto end
)
if "%choice%"=="0" exit
echo 无效选择，请重新输入。
:end
pause
goto menu
