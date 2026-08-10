@echo off
chcp 65001 >nul
title 副机端 Agent（服务端 · 后台）菜单
:menu
cls
echo ============================================
echo        副机端 Agent（采集 + WS/REST 服务）
echo        （普通权限可运行基本采集；温度/帧率建议管理员）
echo ============================================
echo  1. 启动 Agent 后台服务（无界面，建议管理员）
echo  2. 启动 Agent + 本机仪表盘（--gui，PyQt5）
echo  3. 安装开机自启动（需管理员，schtasks /RL HIGHEST）
echo  4. 卸载开机自启动
echo  0. 退出
echo ============================================
set /p choice=请选择:

if "%choice%"=="1" (
    python -m agent
    goto end
)
if "%choice%"=="2" (
    python -m agent --gui
    goto end
)
if "%choice%"=="3" (
    python -m agent --install-startup
    goto end
)
if "%choice%"=="4" (
    python -m agent --remove-startup
    goto end
)
if "%choice%"=="0" exit
echo 无效选择，请重新输入。
:end
pause
goto menu
