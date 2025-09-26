@echo off
chcp 65001 > nul
title 发票合并工具 - 拖放版

echo.
echo ====================================
echo    发票合并工具 v4.0 - 拖放版
echo ====================================
echo.
echo 正在启动程序...
echo.

python merge_invoices_dragdrop.py

if errorlevel 1 (
    echo.
    echo 程序启动失败，请检查：
    echo 1. 是否已安装Python 3
    echo 2. 是否已安装所需依赖库
    echo.
    echo 按任意键退出...
    pause > nul
)