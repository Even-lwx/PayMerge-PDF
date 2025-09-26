@echo off
chcp 65001 > nul
title 打包发票合并工具

echo.
echo ========================================
echo      发票合并工具 - 自动打包脚本
echo ========================================
echo.

echo [1/3] 清理旧文件...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist __pycache__ rmdir /s /q __pycache__
if exist *.spec del *.spec

echo.
echo [2/3] 打包拖放版本...
pyinstaller --onefile ^
    --windowed ^
    --name "发票合并工具-拖放版v4.0" ^
    --add-data "merge_invoices_simple.py;." ^
    --hidden-import tkinterdnd2 ^
    --hidden-import PIL ^
    --hidden-import pypdfium2 ^
    merge_invoices_dragdrop.py

if errorlevel 1 (
    echo.
    echo ❌ 拖放版本打包失败！
    pause
    exit /b 1
)

echo.
echo [3/3] 打包传统版本...
pyinstaller --onefile ^
    --windowed ^
    --name "发票合并工具-传统版v3.0" ^
    --add-data "merge_invoices.py;." ^
    --hidden-import PIL ^
    --hidden-import pypdfium2 ^
    merge_invoices_gui.py

if errorlevel 1 (
    echo.
    echo ❌ 传统版本打包失败！
    pause
    exit /b 1
)

echo.
echo ========================================
echo      ✅ 打包完成！
echo ========================================
echo.
echo 生成的文件位于: dist\ 目录
echo - 发票合并工具-拖放版v4.0.exe (支持拖放，无需文件命名规则)
echo - 发票合并工具-传统版v3.0.exe (需要特定文件命名规则)
echo.
echo 按任意键退出...
pause > nul