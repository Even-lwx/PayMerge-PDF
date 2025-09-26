#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
发票合并工具 v5.0 稳定版 - 打包脚本
使用 PyInstaller 将程序打包为 exe 可执行文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def check_dependencies():
    """检查依赖是否安装"""
    print("🔍 检查依赖库...")
    
    required_packages = [
        'PyInstaller',
        'PyPDF2', 
        'Pillow',
        'pypdfium2',
        'tkinterdnd2'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.lower().replace('-', '_'))
            print(f"✅ {package} - 已安装")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} - 未安装")
    
    if missing_packages:
        print(f"\n⚠️ 缺少依赖: {', '.join(missing_packages)}")
        print("正在自动安装...")
        
        for package in missing_packages:
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                             check=True, capture_output=True, text=True)
                print(f"✅ {package} 安装成功")
            except subprocess.CalledProcessError as e:
                print(f"❌ {package} 安装失败: {e}")
                return False
    
    return True


def create_build_command():
    """创建 PyInstaller 打包命令"""
    
    # 基本参数
    cmd = [
        'pyinstaller',
        '--onefile',                    # 打包为单个exe文件
        '--windowed',                   # 隐藏控制台窗口
        '--name=发票合并工具v5稳定版',      # 设置exe文件名
        '--icon=NONE',                  # 暂不使用图标
        '--distpath=dist',              # 输出目录
        '--workpath=build',             # 临时文件目录
        '--specpath=.',                 # spec文件位置
    ]
    
    # 添加隐式导入（确保所有依赖都被包含）
    hidden_imports = [
        'PIL._tkinter_finder',
        'tkinter',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'PyPDF2',
        'pypdfium2',
        'csv',
        'json',
        're',
        'datetime',
        'tempfile',
        'shutil',
        'threading',
        'pathlib'
    ]
    
    for imp in hidden_imports:
        cmd.extend(['--hidden-import', imp])
    
    # 添加数据文件（如果有）
    if os.path.exists('merge_invoices_simple.py'):
        cmd.extend(['--add-data', 'merge_invoices_simple.py;.'])
    
    # 添加主程序文件
    cmd.append('invoice_merger_v5_stable.py')
    
    return cmd


def build_executable():
    """执行打包过程"""
    print("\n🚀 开始打包程序...")
    
    try:
        # 创建打包命令
        cmd = create_build_command()
        print(f"💻 执行命令: {' '.join(cmd)}")
        
        # 执行打包
        result = subprocess.run(cmd, capture_output=True, text=True, cwd='.')
        
        if result.returncode == 0:
            print("✅ 打包成功！")
            
            # 检查输出文件
            exe_path = os.path.join('dist', '发票合并工具v5稳定版.exe')
            if os.path.exists(exe_path):
                file_size = os.path.getsize(exe_path) / 1024 / 1024  # MB
                print(f"📦 生成的exe文件: {exe_path}")
                print(f"📏 文件大小: {file_size:.1f} MB")
                
                # 创建运行目录
                release_dir = "发票合并工具v5稳定版_发布包"
                if os.path.exists(release_dir):
                    shutil.rmtree(release_dir)
                os.makedirs(release_dir)
                
                # 复制exe文件
                shutil.copy2(exe_path, release_dir)
                
                # 创建使用说明
                create_readme(release_dir)
                
                print(f"🎉 发布包已准备完成: {release_dir}/")
                return True
            else:
                print("❌ 找不到生成的exe文件")
                return False
                
        else:
            print("❌ 打包失败!")
            print("错误输出:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 打包过程出现异常: {e}")
        return False


def create_readme(output_dir):
    """创建使用说明文件"""
    readme_content = """# 发票合并工具 v5.0 稳定版

## 📋 使用说明

1. **双击运行**：直接双击 `发票合并工具v5稳定版.exe` 即可启动
2. **选择文件**：
   - 拖拽或点击按钮选择 1个PDF发票文件
   - 拖拽或点击按钮选择 2张图片文件（购买记录 + 支付记录）
3. **提取数据**：点击【提取数据】按钮自动识别发票信息
4. **智能合并**：点击【智能合并】生成最终PDF文件

## ✨ 核心功能

- 🔍 **智能数据提取**：自动识别发票号、日期、金额
- 📝 **智能命名**：格式为 `日期_金额_发票号后4位_已合并.pdf`
- 📊 **CSV汇总**：自动记录所有处理过的发票到CSV文件
- 🎯 **拖拽支持**：支持文件拖拽操作

## 📝 文件命名示例

- `20250926_199元_#5678_已合并.pdf`
- `20251231_355.50元_#5432_已合并.pdf`

## 📊 汇总文件

程序会自动在exe同目录下生成 `发票汇总记录.csv` 文件，记录所有处理过的发票信息。

## ❓ 常见问题

1. **杀毒软件误报**：exe文件可能被杀毒软件误判，请添加信任
2. **文件路径问题**：建议将文件放在英文路径下运行
3. **权限问题**：如遇到权限问题，请右键"以管理员身份运行"

## 🔧 技术信息

- 基于Python开发，使用PyInstaller打包
- 包含所有必要依赖，无需额外安装
- 支持Windows 10/11系统

---
版本：v5.0 稳定版
更新日期：2025年9月26日
"""
    
    readme_path = os.path.join(output_dir, "使用说明.txt")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"📄 使用说明已创建: {readme_path}")


def cleanup():
    """清理临时文件"""
    print("\n🧹 清理临时文件...")
    
    cleanup_dirs = ['build', '__pycache__']
    cleanup_files = ['发票合并工具v5稳定版.spec']
    
    for dir_name in cleanup_dirs:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"🗑️ 删除目录: {dir_name}")
    
    for file_name in cleanup_files:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"🗑️ 删除文件: {file_name}")


def main():
    """主函数"""
    print("=" * 60)
    print("📦 发票合并工具 v5.0 稳定版 - 打包程序")
    print("=" * 60)
    
    # 检查当前目录
    if not os.path.exists('invoice_merger_v5_stable.py'):
        print("❌ 找不到主程序文件 invoice_merger_v5_stable.py")
        print("请在包含主程序文件的目录下运行此脚本")
        return 1
    
    # 检查依赖
    if not check_dependencies():
        print("❌ 依赖检查失败，无法继续打包")
        return 1
    
    # 执行打包
    if build_executable():
        cleanup()
        print("\n🎉 打包完成！")
        print("📁 发布包位置: 发票合并工具v5稳定版_发布包/")
        print("💡 可以将整个文件夹分发给其他用户使用")
        return 0
    else:
        print("\n❌ 打包失败")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        input("\n按回车键退出...")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️ 用户取消操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        input("\n按回车键退出...")
        sys.exit(1)