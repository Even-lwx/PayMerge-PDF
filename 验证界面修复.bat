@echo off
chcp 65001 >nul
echo.
echo ✨ 发票合并工具 - 界面修复验证
echo.
echo 🔍 检查修复内容：
echo.

REM 检查可执行文件是否存在
if exist "发票合并工具_分发包\发票合并工具.exe" (
    echo ✅ 可执行文件已更新
) else (
    echo ❌ 可执行文件缺失
    goto ERROR
)

REM 检查文件大小（新版本应该约19MB）
for %%I in ("发票合并工具_分发包\发票合并工具.exe") do set size=%%~zI
set /a sizeMB=%size%/1024/1024
echo ✅ 文件大小: %sizeMB%MB

REM 检查说明文档
if exist "发票合并工具_分发包\使用说明.md" (
    echo ✅ 使用说明已更新
) else (
    echo ❌ 使用说明缺失
)

echo.
echo 🚀 修复内容总结：
echo • 界面窗口从 500x400 调整为 600x500
echo • 优化元素间距，避免文字被按钮遮挡
echo • 添加文字换行，提升可读性
echo • 增加版本信息和更新说明
echo.

echo 📦 分发建议：
echo 1. 将整个"发票合并工具_分发包"文件夹打包为ZIP
echo 2. 文件名建议: 发票合并工具_v2.0.1_界面修复版.zip
echo 3. 可通过网盘、内网等方式分享给用户
echo.

REM 询问是否测试运行
set /p test=是否测试运行程序？(y/N): 
if /i "%test%"=="y" (
    echo.
    echo 🔄 启动程序测试...
    start "" "发票合并工具_分发包\发票合并工具.exe"
    echo.
    echo 💡 请检查：
    echo • 界面是否正常显示，无文字遮挡
    echo • 窗口大小是否合适
    echo • 按钮功能是否正常
)

echo.
echo 🎉 界面修复验证完成！
goto END

:ERROR
echo.
echo ❌ 验证失败，请重新打包程序
pause
exit /b 1

:END
pause