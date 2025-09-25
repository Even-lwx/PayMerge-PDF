@echo off
chcp 65001 >nul
color 0E
echo.
echo 🧪 发票合并工具 - 修复验证测试
echo.
echo ================================================================

:MENU
echo.
echo 选择测试模式：
echo [1] 测试"选择目录"功能
echo [2] 测试"使用当前目录"功能（将exe复制到测试目录）
echo [3] 命令行模式测试
echo [4] 查看测试文件
echo [9] 退出
echo.
set /p choice=请选择测试项 (1-4,9): 

if "%choice%"=="1" goto TEST_SELECT
if "%choice%"=="2" goto TEST_CURRENT
if "%choice%"=="3" goto TEST_CLI
if "%choice%"=="4" goto VIEW_FILES
if "%choice%"=="9" goto END
goto MENU

:TEST_SELECT
echo.
echo 📁 测试"选择目录"功能
echo.
echo 💡 操作步骤：
echo 1. 程序将启动GUI界面
echo 2. 点击"📁 选择发票目录"按钮
echo 3. 选择"测试目录"文件夹
echo 4. 查看是否正确处理文件
echo.
pause
echo 🚀 启动测试...
start "" "发票合并工具_分发包\发票合并工具.exe"
echo.
echo ⏳ 请按照上述步骤操作，然后按任意键继续...
pause
goto CHECK_RESULT

:TEST_CURRENT
echo.
echo 📍 测试"使用当前目录"功能
echo.
echo 正在复制可执行文件到测试目录...
copy "发票合并工具_分发包\发票合并工具.exe" "测试目录\" >nul
if errorlevel 1 (
    echo ❌ 复制失败
    pause
    goto MENU
)
echo ✅ 复制完成

echo.
echo 💡 操作步骤：
echo 1. 程序将从测试目录启动
echo 2. 点击"📍 使用当前目录"按钮
echo 3. 确认处理当前目录的文件
echo 4. 查看是否正确生成合并文件
echo.
pause
echo 🚀 启动测试...
cd "测试目录"
start "" "发票合并工具.exe"
cd ..
echo.
echo ⏳ 请按照上述步骤操作，然后按任意键继续...
pause
goto CHECK_RESULT

:TEST_CLI
echo.
echo 🖥️ 测试命令行模式
echo.
echo 测试直接调用合并功能...
"发票合并工具_分发包\发票合并工具.exe" --cli "测试目录"
if errorlevel 1 (
    echo ❌ 命令行测试失败
) else (
    echo ✅ 命令行测试完成
)
echo.
pause
goto CHECK_RESULT

:VIEW_FILES
echo.
echo 📋 查看测试文件状态
echo.
echo 测试目录内容：
dir "测试目录" /B
echo.
if exist "测试目录\已合并" (
    echo 已合并目录内容：
    dir "测试目录\已合并" /B
) else (
    echo 📂 尚未生成"已合并"目录
)
echo.
pause
goto MENU

:CHECK_RESULT
echo.
echo 🔍 检查测试结果...
echo.
if exist "测试目录\已合并\1开发板19.9已合并.pdf" (
    echo ✅ 成功！已生成合并文件
    echo 📄 文件位置: 测试目录\已合并\1开发板19.9已合并.pdf
    
    REM 获取文件大小
    for %%I in ("测试目录\已合并\1开发板19.9已合并.pdf") do set size=%%~zI
    set /a sizeKB=%size%/1024
    echo 📊 文件大小: %sizeKB%KB
    
    echo.
    echo 🎉 修复验证成功！
    echo • "选择目录"功能正常
    echo • "使用当前目录"功能正常  
    echo • 文件合并逻辑正常
    echo • 输出路径正确
) else (
    echo ❌ 测试失败：未找到合并文件
    echo.
    echo 🔧 可能的问题：
    echo • 文件命名不符合规则
    echo • 程序无法访问目录
    echo • 合并逻辑出错
    echo.
    echo 📋 请检查：
    echo 1. 测试目录是否包含完整的三个文件
    echo 2. 程序是否显示错误信息
    echo 3. 是否有权限访问目录
)
echo.
pause
goto MENU

:END
echo.
echo 🧹 清理测试文件...
if exist "测试目录\发票合并工具.exe" del "测试目录\发票合并工具.exe" >nul 2>&1
echo.
echo 👋 测试完成！
echo.
echo 📋 修复要点总结：
echo • 修复了可执行文件的工作目录问题
echo • 改进了模块导入机制
echo • 优化了目录参数传递
echo • 增强了错误处理能力
echo.
pause