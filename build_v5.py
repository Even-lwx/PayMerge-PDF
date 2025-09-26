"""
发票合并工具打包脚本 v5.0
基于v4.0拖放版升级，新增智能数据提取功能

新功能特性：
- 智能发票数据提取（发票号、日期、金额、公司信息）
- 智能文件重命名
- CSV汇总文件持续记录
- 基于pypdfium2的高质量PDF文本解析

使用方法:
1. 确保已安装所有依赖: pip install pypdfium2 tkinterdnd2
2. 安装 PyInstaller: pip install pyinstaller
3. 运行打包脚本: python build_v5.py

生成的可执行文件将在 dist/ 目录下
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description=""):
    """运行命令并检查结果"""
    print(f"执行: {description}")
    print(f"命令: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True, encoding='utf-8')
        print("✓ 成功")
        if result.stdout:
            print(f"输出: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 失败: {e}")
        if e.stdout:
            print(f"标准输出: {e.stdout}")
        if e.stderr:
            print(f"错误输出: {e.stderr}")
        return False

def check_pyinstaller():
    """检查 PyInstaller 是否已安装"""
    try:
        subprocess.run([sys.executable, "-c", "import PyInstaller"], 
                      check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False

def build_executable():
    """构建可执行文件"""
    script_dir = Path(__file__).parent
    main_script = script_dir / "invoice_merger_v5.py"
    
    if not main_script.exists():
        print(f"错误: 找不到主脚本文件 {main_script}")
        return False
    
    # 检查 PyInstaller
    if not check_pyinstaller():
        print("PyInstaller 未安装，正在安装...")
        if not run_command(f"{sys.executable} -m pip install pyinstaller", "安装 PyInstaller"):
            return False
    
    # PyInstaller 命令参数
    cmd_parts = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                          # 打包成单个文件
        "--windowed",                         # Windows下不显示控制台窗口
        "--name", "发票合并工具_v5.0_智能版",    # 可执行文件名称
        "--add-data", "merge_invoices_simple.py;.",  # 添加合并逻辑
        "--hidden-import", "PIL._tkinter_finder",    # 确保PIL正常工作
        "--hidden-import", "pypdfium2",              # PDF处理库
        "--hidden-import", "tkinterdnd2",            # 拖放功能库
        "--hidden-import", "tkinter",                # GUI库
        "--clean",                            # 清理临时文件
        str(main_script)
    ]
    
    cmd = " ".join(f'"{part}"' if " " in part else part for part in cmd_parts)
    
    if run_command(cmd, "打包可执行文件"):
        print("\n✓ 打包完成！")
        print(f"可执行文件位置: {script_dir / 'dist' / '发票合并工具_v5.0_智能版.exe'}")
        print("\n✨ v5.0 版本特性:")
        print("• 🔍 智能发票数据提取 - 自动识别关键信息")
        print("• 📝 智能文件重命名 - 基于发票内容生成文件名")
        print("• 📊 CSV汇总记录 - 持续追加发票数据")
        print("• 🎯 保持v4.0拖放功能 - 完全兼容原有操作")
        print("• 🏢 企业信息识别 - 公司名称和税号提取")
        print("\n使用说明:")
        print("1. 双击运行可执行文件")
        print("2. 拖放PDF发票和2张图片到界面")
        print("3. 程序自动提取数据并显示预览")
        print("4. 点击【智能合并】完成处理")
        print("5. 自动生成智能命名的PDF和CSV汇总记录")
        return True
    else:
        print("\n✗ 打包失败")
        return False

def create_spec_file():
    """创建 PyInstaller 配置文件"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['invoice_merger_v5.py'],
    pathex=[],
    binaries=[],
    datas=[('merge_invoices_simple.py', '.')],
    hiddenimports=['PIL._tkinter_finder', 'pypdfium2', 'tkinterdnd2', 'tkinter'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='发票合并工具_v5.0_智能版',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
'''
    
    with open('发票合并工具_v5.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print("✓ 已创建 PyInstaller 配置文件: 发票合并工具_v5.spec")

if __name__ == "__main__":
    print("=== 发票合并工具 v5.0 打包脚本 ===\n")
    print("🚀 基于v4.0拖放版升级，新增智能数据提取功能")
    print("="*50)
    
    # 创建spec配置文件
    create_spec_file()
    
    # 执行打包
    success = build_executable()
    
    if success:
        print("\n🎉 v5.0 智能版打包成功！")
        print("\n📋 版本升级亮点:")
        print("✅ 保持v4.0所有拖放功能")
        print("✅ 新增发票数据自动提取")
        print("✅ 智能文件命名系统")
        print("✅ CSV汇总持续记录")
        print("✅ 企业级数据管理功能")
        print("\n分发建议:")
        print("- 可执行文件独立运行，无需Python环境")
        print("- 包含所有依赖库，约30-40MB")
        print("- 支持Windows 7及以上版本")
        print("- 自动生成发票汇总记录.csv文件")
    else:
        print("\n❌ 打包过程中出现错误，请检查上述输出")
        print("请确保已安装依赖：pip install pypdfium2 tkinterdnd2")
    
    input("\n按回车键退出...")