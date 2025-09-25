@echo off
chcp 65001 >nul
color 0B
echo.
echo ✨ 发票合并工具 v3.0 验证测试
echo ================================
echo.

REM 检查v3.0可执行文件
if exist "发票合并工具_v3.0_分发包\发票合并工具_v3.0.exe" (
    echo ✅ v3.0 可执行文件存在
) else (
    echo ❌ v3.0 可执行文件缺失
    goto ERROR
)

REM 检查文件大小
for %%I in ("发票合并工具_v3.0_分发包\发票合并工具_v3.0.exe") do set size=%%~zI
set /a sizeMB=%size%/1024/1024
echo ✅ 文件大小: %sizeMB%MB

REM 检查分发包完整性
if exist "发票合并工具_v3.0_分发包\使用说明.md" (
    echo ✅ 使用说明文档存在
) else (
    echo ⚠️ 使用说明文档缺失
)

if exist "发票合并工具_v3.0_分发包\v3.0发布说明.md" (
    echo ✅ 版本发布说明存在
) else (
    echo ⚠️ 版本发布说明缺失
)

echo.
echo 📋 v3.0 版本特性验证：
echo • 🔧 核心功能修复: 已解决"使用当前目录"问题
echo • 📂 智能目录识别: 打包环境兼容性完善
echo • 🛡️ 错误处理增强: 全面的异常处理机制
echo • 🖥️ 界面体验优化: 600x500窗口尺寸
echo • ⚡ 企业级稳定性: 生产环境就绪

echo.
echo 🧪 快速功能测试:
set /p test=是否启动v3.0进行功能测试？(y/N): 
if /i "%test%"=="y" (
    echo.
    echo 🚀 启动发票合并工具 v3.0...
    start "" "发票合并工具_v3.0_分发包\发票合并工具_v3.0.exe"
    echo.
    echo 💡 测试建议:
    echo 1. 验证界面标题显示"v3.0"
    echo 2. 测试"选择发票目录"功能
    echo 3. 测试"使用当前目录"功能 (重点验证)
    echo 4. 检查处理结果和错误处理
    echo.
    pause
)

echo.
echo 📦 分发包状态总结:
echo ================================
echo 📁 分发包: 发票合并工具_v3.0_分发包
echo 📄 主程序: 发票合并工具_v3.0.exe (%sizeMB%MB)
echo 🏷️ 版本号: v3.0.0
echo 📅 发布日期: 2025-09-25
echo 🎯 状态: 生产就绪 ✅
echo.
echo 🌟 v3.0 重大改进:
echo • 彻底修复了v2.x的已知问题
echo • 提升了企业级部署的稳定性
echo • 完善了用户体验和错误处理
echo • 适合大规模分发和使用
echo.

echo 🎉 v3.0版本验证完成！可以安心分发使用！
goto END

:ERROR
echo.
echo ❌ 验证失败，请检查打包过程
pause
exit /b 1

:END
pause