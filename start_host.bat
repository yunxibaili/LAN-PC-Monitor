@echo off
chcp 65001 >nul
title 监控主机（Host · 集中显示）菜单
:menu
cls
echo ============================================
echo        监控主机（Host · 集中显示 GUI）
echo        显示所有节点 + 本机节点
echo ============================================
echo  1. 启动监控主机
echo  2. 安装开机自启动（注册表，无需管理员）
echo  3. 卸载开机自启动
echo  0. 退出
echo ============================================
set /p choice=请选择:

if "%choice%"=="1" (
    python -m host
    goto end
)
if "%choice%"=="2" (
    python -m host --install-startup
    goto end
)
if "%choice%"=="3" (
    python -m host --remove-startup
    goto end
)
if "%choice%"=="0" exit
echo 无效选择，请重新输入。
:end
pause
goto menu
