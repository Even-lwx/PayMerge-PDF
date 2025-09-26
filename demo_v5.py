#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
发票合并工具 v5.0 功能演示脚本
展示基于v4.0升级后的智能数据提取功能
"""

import os
import sys
from pathlib import Path
import json
from datetime import datetime

def demo_v5_features():
    """演示 v5.0 新功能"""
    print("🎯 发票合并工具 v5.0 - 智能数据提取版")
    print("基于 v4.0 拖放版升级")
    print("=" * 60)
    
    print("\n📋 版本演进路径:")
    print("v3.0 (GUI基础版) → v4.0 (拖放版) → v5.0 (智能数据提取版)")
    
    print("\n🆕 v5.0 新增功能:")
    features = [
        "🔍 智能发票数据提取",
        "  • 发票号码自动识别",
        "  • 开票日期智能解析",
        "  • 金额精确提取",
        "  • 企业信息识别",
        "  • 纳税人识别号提取",
        "",
        "📝 智能文件重命名",
        "  • 基于发票内容生成文件名",
        "  • 格式：日期_销售方_金额_发票号",
        "  • 自动去除特殊字符",
        "",
        "📊 CSV汇总记录功能",
        "  • 持续追加发票记录",
        "  • Excel兼容格式",
        "  • 包含完整发票信息",
        "  • 支持数据分析和统计",
        "",
        "🎯 完全保持v4.0功能",
        "  • 拖放操作界面",
        "  • 文件选择功能",
        "  • 合并处理逻辑",
        "  • 用户体验一致"
    ]
    
    for feature in features:
        print(feature)
    
    print("\n🔧 技术升级:")
    tech_features = [
        "📄 pypdfium2库 - 高质量PDF文本提取",
        "🧠 智能正则匹配 - 多模式数据识别",
        "📊 CSV自动管理 - 持续数据汇总",
        "🎨 分页界面设计 - 数据预览和命名预览",
        "⚡ 后台处理线程 - 界面响应流畅"
    ]
    
    for tech in tech_features:
        print(tech)
    
    print("\n🎮 使用流程:")
    steps = [
        "1. 启动 v5.0 智能版程序",
        "2. 拖放 PDF发票 + 2张图片到界面",
        "3. 程序自动提取发票数据并显示预览",
        "4. 查看智能生成的文件命名方案",
        "5. 点击【智能合并】按钮完成处理",
        "6. 自动保存合并PDF和更新CSV汇总记录"
    ]
    
    for step in steps:
        print(step)
    
    print("\n📊 输出文件:")
    outputs = [
        "📄 智能命名的合并PDF文件",
        "   例：20250926_某某公司_19.90元_#3789_已合并.pdf",
        "",
        "📊 发票汇总记录.csv",
        "   包含：发票号、日期、金额、公司、原文件名等",
        "   持续追加，支持Excel打开分析"
    ]
    
    for output in outputs:
        print(output)
    
    print("\n🎯 智能命名示例:")
    examples = [
        {
            "原文件": "1开发板19.9.pdf",
            "提取数据": {
                "日期": "2025-09-18",
                "销售方": "深圳市某某电子有限公司",  
                "金额": 19.90,
                "发票号": "25957000000129353789"
            },
            "智能命名": "20250918_深圳市某某电子_19.90元_#3789_已合并.pdf"
        },
        {
            "原文件": "TC264学习板355.pdf",
            "提取数据": {
                "日期": "2025-09-23",
                "销售方": "某某科技有限公司",
                "金额": 355.00, 
                "发票号": "25512000000225368467"
            },
            "智能命名": "20250923_某某科技_355.00元_#8467_已合并.pdf"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n示例 {i}:")
        print(f"  原文件名: {example['原文件']}")
        print(f"  提取数据: 日期={example['提取数据']['日期']}, "
              f"公司={example['提取数据']['销售方'][:8]}..., "
              f"金额={example['提取数据']['金额']}")
        print(f"  智能命名: {example['智能命名']}")
    
    print("\n" + "=" * 60)
    print("✨ v5.0 = v4.0 拖放体验 + 智能数据处理 + 自动化管理")
    print("🎉 在保持原有操作习惯的基础上，大幅提升数据处理效率！")

def check_dependencies():
    """检查依赖库状态"""
    print("\n🔍 依赖库检查:")
    
    # 检查 pypdfium2
    try:
        import pypdfium2
        print("✅ pypdfium2 - PDF文本提取库已安装")
    except ImportError:
        print("❌ pypdfium2 - 需要安装: pip install pypdfium2")
    
    # 检查 tkinterdnd2  
    try:
        import tkinterdnd2
        print("✅ tkinterdnd2 - 拖放功能库已安装")
    except ImportError:
        print("❌ tkinterdnd2 - 需要安装: pip install tkinterdnd2")
    
    # 检查源文件
    script_dir = Path(__file__).parent
    files_to_check = [
        "invoice_merger_v5.py",
        "merge_invoices_dragdrop.py", 
        "1开发板19.9.pdf",
        "2TC264学习板核心板355.pdf"
    ]
    
    print("\n📁 文件检查:")
    for file_name in files_to_check:
        file_path = script_dir / file_name
        if file_path.exists():
            print(f"✅ {file_name}")
        else:
            print(f"❌ {file_name} - 文件不存在")

if __name__ == "__main__":
    try:
        demo_v5_features()
        check_dependencies()
        
        print(f"\n📍 当前工作目录: {os.getcwd()}")
        print(f"⏰ 演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n🚀 准备就绪！现在可以:")
        print("1. 运行 python invoice_merger_v5.py 启动v5.0源码版")
        print("2. 运行 python build_v5.py 打包生成可执行文件")
        print("3. 直接运行可执行文件进行测试")
        
        input("\n按回车键退出...")
        
    except Exception as e:
        print(f"❌ 演示脚本执行失败: {e}")
        input("\n按回车键退出...")
        sys.exit(1)