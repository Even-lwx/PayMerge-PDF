@echo off
chcp 65001 >nul
color 0A
echo.
echo ██╗███╗   ██╗██╗   ██╗ ██████╗ ██╗ ██████╗███████╗
echo ██║████╗  ██║██║   ██║██╔═══██╗██║██╔════╝██╔════╝
echo ██║██╔██╗ ██║██║   ██║██║   ██║██║██║     █████╗  
echo ██║██║╚██╗██║╚██╗ ██╔╝██║   ██║██║██║     ██╔══╝  
echo ██║██║ ╚████║ ╚████╔╝ ╚██████╔╝██║╚██████╗███████╗
echo ╚═╝╚═╝  ╚═══╝  ╚═══╝   ╚═════╝ ╚═╝ ╚═════╝╚══════╝
echo.
echo           发票合并工具 - 完整打包脚本 v2.0
echo.
echo ================================================================

:MENU
echo.
echo 请选择操作：
echo [1] 全新打包（推荐）
echo [2] 只更新可执行文件  
echo [3] 创建分发压缩包
echo [4] 清理临时文件
echo [9] 退出
echo.
set /p choice=请输入选项 (1-4,9): 

if "%choice%"=="1" goto FULL_BUILD
if "%choice%"=="2" goto BUILD_ONLY
if "%choice%"=="3" goto CREATE_DIST
if "%choice%"=="4" goto CLEANUP
if "%choice%"=="9" goto END
goto MENU

:FULL_BUILD
echo.
echo ✨ 开始全新打包...
echo.

echo 📋 第1步：环境检查
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python 3.7+
    echo 💡 下载地址: https://www.python.org/downloads/
    pause
    goto MENU
)
echo ✅ Python环境正常

echo.
echo 📋 第2步：安装依赖
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements-build.txt
if errorlevel 1 (
    echo ❌ 依赖安装失败
    pause
    goto MENU
)
echo ✅ 依赖安装完成

echo.
echo 📋 第3步：执行打包
python build.py
if errorlevel 1 (
    echo ❌ 打包失败，请检查错误信息
    pause
    goto MENU
)

echo.
echo 📋 第4步：创建分发包
goto CREATE_DIST

:BUILD_ONLY
echo.
echo 🔄 仅重新打包可执行文件...
python build.py
goto MENU

:CREATE_DIST
echo.
echo 📦 创建分发包...

REM 清理旧的分发包
if exist "发票合并工具_分发包" (
    rmdir /s /q "发票合并工具_分发包" >nul 2>&1
)

REM 创建分发目录
mkdir "发票合并工具_分发包" >nul 2>&1

REM 复制文件
if exist "dist\发票合并工具.exe" (
    copy "dist\发票合并工具.exe" "发票合并工具_分发包\" >nul
    echo ✅ 可执行文件已复制
) else (
    echo ❌ 找不到可执行文件，请先执行打包
    pause
    goto MENU
)

copy "使用说明.md" "发票合并工具_分发包\" >nul 2>&1

REM 创建版本信息文件
echo 发票合并工具 v2.0 > "发票合并工具_分发包\版本信息.txt"
echo 打包时间: %DATE% %TIME% >> "发票合并工具_分发包\版本信息.txt"
echo 文件大小: >> "发票合并工具_分发包\版本信息.txt"
dir "发票合并工具_分发包\发票合并工具.exe" | find ".exe" >> "发票合并工具_分发包\版本信息.txt"

REM 创建压缩包（如果有7zip或winrar）
where 7z >nul 2>&1
if not errorlevel 1 (
    echo.
    echo 🗜️ 创建ZIP压缩包...
    7z a -tzip "发票合并工具_v2.0.zip" "发票合并工具_分发包\*" >nul
    echo ✅ 已创建: 发票合并工具_v2.0.zip
)

echo.
echo 🎉 分发包创建完成！
echo.
echo 📁 分发包位置: %CD%\发票合并工具_分发包
echo 📦 压缩包位置: %CD%\发票合并工具_v2.0.zip (如果已创建)
echo.
echo 📋 分发包内容:
dir "发票合并工具_分发包"
echo.
echo 💡 提示:
echo    - 可执行文件大小约19MB
echo    - 支持Windows 7及以上系统
echo    - 绿色软件，无需安装
echo    - 建议分发压缩包版本
echo.
pause
goto MENU

:CLEANUP
echo.
echo 🧹 清理临时文件...
if exist "build" rmdir /s /q "build" >nul 2>&1
if exist "__pycache__" rmdir /s /q "__pycache__" >nul 2>&1
if exist "*.spec" del /q "*.spec" >nul 2>&1
echo ✅ 临时文件已清理
pause
goto MENU

:END
echo.
echo 👋 感谢使用发票合并工具打包脚本！
echo.
echo 🔗 如需技术支持，请联系开发者
echo 📧 问题反馈: 请提供详细的错误信息和系统环境
echo.
pause
exit