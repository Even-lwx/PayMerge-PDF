@echo off
chcp 65001 >nul
title 发票合并工具v5.0稳定版

echo ===============================================
echo        🚀 发票合并工具 v5.0 稳定版
echo ===============================================
echo.
echo ✨ 智能功能：
echo    🔍 自动提取发票数据
echo    📝 智能文件命名：日期_金额_发票号后4位
echo    📊 CSV自动汇总记录
echo    🎯 支持拖拽操作
echo.
echo 💡 正在启动程序，请稍候...
echo.

REM 启动程序
"发票合并工具v5稳定版.exe"

REM 程序结束后的提示
echo.
echo 📋 程序已退出
echo    汇总记录保存在：发票汇总记录.csv
echo.
pause