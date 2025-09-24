@echo off
chcp 65001 >nul
echo === 发票合并工具一键打包脚本 ===
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.7或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✓ Python环境检查通过

REM 安装依赖
echo.
echo 正在安装依赖包...
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt

if errorlevel 1 (
    echo.
    echo 错误: 依赖安装失败
    pause
    exit /b 1
)

echo ✓ 依赖安装完成

REM 执行打包
echo.
echo 开始打包...
python build.py

echo.
echo 打包完成！查看dist目录下的可执行文件。
pause