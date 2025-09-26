@echo off
title 发票合并工具 v5.0

echo 🚀 启动发票合并工具 v5.0 智能数据提取版...
echo.

python "%~dp0invoice_merger_v5.py"

if %errorlevel% neq 0 (
    echo.
    echo ❌ 程序异常退出
    pause
)