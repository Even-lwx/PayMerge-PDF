@echo off
chcp 65001 >nul
title 发票合并工具 v5.0 - 智能数据提取版

cls
echo.
echo ===============================================
echo    📄 发票合并工具 v5.0 - 智能数据提取版
echo ===============================================
echo.
echo 🚀 基于 v4.0 拖放版升级
echo.
echo ✨ 新功能特色：
echo   🔍 智能发票数据提取
echo   📝 智能文件重命名  
echo   📊 CSV汇总记录
echo   🎯 保持拖放体验
echo.
echo ===============================================

echo 🔄 正在启动程序...
python "%~dp0invoice_merger_v5.py"

if %errorlevel% neq 0 (
    echo.
    echo ❌ 启动失败！可能的原因：
    echo   • 缺少依赖库：pip install pypdfium2 tkinterdnd2
    echo   • Python环境问题
    echo.
    pause
) else (
    echo.
    echo ✅ 程序已正常退出
)

echo.
pause