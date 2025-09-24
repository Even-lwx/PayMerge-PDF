"""
发票合并工具打包脚本
使用 PyInstaller 将 Python 脚本打包为独立可执行文件

使用方法:
1. 确保已安装所有依赖: pip install -r requirements.txt
2. 安装 PyInstaller: pip install pyinstaller
3. 运行打包脚本: python build.py

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
    main_script = script_dir / "merge_invoices_gui.py"
    
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
        "--onefile",                    # 打包成单个文件
        "--windowed",                   # Windows下不显示控制台窗口
        "--name", "发票合并工具",         # 可执行文件名称
        "--add-data", "merge_invoices.py;.",      # 添加原始脚本
        "--add-data", "README.md;.",              # 添加README到打包文件
        "--hidden-import", "PIL._tkinter_finder", # 确保PIL正常工作
        "--hidden-import", "pypdfium2",           # 确保pypdfium2正常工作
        "--hidden-import", "tkinter",             # 确保tkinter正常工作
        "--clean",                      # 清理临时文件
        str(main_script)
    ]
    
    cmd = " ".join(f'"{part}"' if " " in part else part for part in cmd_parts)
    
    if run_command(cmd, "打包可执行文件"):
        print("\n✓ 打包完成！")
        print(f"可执行文件位置: {script_dir / 'dist' / '发票合并工具.exe'}")
        print("\n使用说明:")
        print("1. 将生成的 '发票合并工具.exe' 复制到包含发票文件的目录")
        print("2. 双击运行即可自动合并发票")
        print("3. 合并后的文件将保存在 '已合并' 子目录中")
        return True
    else:
        print("\n✗ 打包失败")
        return False

def create_spec_file():
    """创建 PyInstaller 配置文件 (可选，用于高级配置)"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['merge_invoices_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('merge_invoices.py', '.'), ('README.md', '.')],
    hiddenimports=['PIL._tkinter_finder', 'pypdfium2', 'tkinter'],
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
    name='发票合并工具',
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
    
    with open('发票合并工具.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print("✓ 已创建 PyInstaller 配置文件: 发票合并工具.spec")

if __name__ == "__main__":
    print("=== 发票合并工具打包脚本 ===\n")
    
    # 创建spec配置文件
    create_spec_file()
    
    # 执行打包
    success = build_executable()
    
    if success:
        print("\n🎉 打包成功完成！")
        print("\n分发建议:")
        print("- 可执行文件可以独立运行，无需安装Python")
        print("- 文件大小约20-50MB，包含所有依赖")
        print("- 支持Windows 7及以上版本")
        print("- 可以通过网盘、U盘等方式分享")
    else:
        print("\n❌ 打包过程中出现错误，请检查上述输出")
    
    input("\n按回车键退出...")