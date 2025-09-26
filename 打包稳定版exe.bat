@echo off
chcp 65001 >nul
echo ================================================================
echo                 发票合并工具 v5.0 稳定版 - 打包程序
echo ================================================================
echo.
echo 正在检查Python环境...

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到Python环境
    echo 💡 请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

echo ✅ Python环境检查通过
echo.

REM 升级pip
echo 🔄 更新pip...
python -m pip install --upgrade pip --quiet

REM 安装必要的依赖
echo 🔄 安装打包依赖...
python -m pip install pyinstaller --quiet

REM 执行打包脚本
echo 🚀 开始打包程序...
echo.
python build_stable_exe.py

echo.
echo ================================================================
echo                            打包完成
echo ================================================================
pause