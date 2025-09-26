#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
发票合并工具 v5.0 功能测试脚本
测试智能数据提取功能
"""

import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

try:
    from invoice_merger_v5 import InvoiceDataExtractor, SmartFileNamer
    print("✅ 成功导入 v5.0 模块")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

def test_invoice_extraction():
    """测试发票数据提取功能"""
    print("\n🔍 测试发票数据提取功能")
    print("=" * 40)
    
    # 测试文件
    test_files = [
        "1开发板19.9.pdf",
        "2TC264学习板核心板355.pdf"
    ]
    
    for pdf_file in test_files:
        if os.path.exists(pdf_file):
            print(f"\n📄 测试文件: {pdf_file}")
            try:
                # 提取数据
                data = InvoiceDataExtractor.extract_invoice_data(pdf_file)
                
                print("提取结果:")
                for key, value in data.items():
                    if key in ['invoice_number', 'invoice_date', 'amount', 'seller_name']:
                        print(f"  {key}: {value}")
                
                # 测试智能命名
                smart_name = SmartFileNamer.generate_smart_filename(data, pdf_file)
                print(f"  智能命名: {smart_name}")
                
                print("✅ 提取成功")
                
            except Exception as e:
                print(f"❌ 提取失败: {e}")
        else:
            print(f"❌ 测试文件不存在: {pdf_file}")

def test_csv_functionality():
    """测试CSV功能"""
    print("\n📊 测试CSV汇总功能")
    print("=" * 40)
    
    try:
        from invoice_merger_v5 import CSVManager
        
        # 创建测试CSV文件
        test_csv = "test_invoice_summary.csv"
        csv_manager = CSVManager(test_csv)
        
        # 测试数据
        test_data = {
            'invoice_number': '12345678901234567890',
            'invoice_date': '2025-09-26',
            'amount': 199.99,
            'seller_name': '测试公司',
            'seller_tax_id': 'TEST123456789',
            'file_name': 'test.pdf'
        }
        
        # 添加记录
        csv_manager.append_invoice_record(test_data, 'test_merged.pdf')
        print(f"✅ 成功创建CSV文件: {test_csv}")
        
        # 读取并显示内容
        if os.path.exists(test_csv):
            with open(test_csv, 'r', encoding='utf-8-sig') as f:
                content = f.read()
                print("CSV内容:")
                print(content)
        
        # 清理测试文件
        if os.path.exists(test_csv):
            os.remove(test_csv)
            print("✅ 清理测试文件完成")
            
    except Exception as e:
        print(f"❌ CSV测试失败: {e}")

def main():
    """主测试函数"""
    print("🎯 发票合并工具 v5.0 功能测试")
    print("基于 v4.0 拖放版升级的智能数据提取版本")
    print("=" * 50)
    
    # 检查依赖
    try:
        import pypdfium2
        print("✅ pypdfium2 已安装")
    except ImportError:
        print("❌ pypdfium2 未安装 - 数据提取功能不可用")
        return
    
    try:
        import tkinterdnd2
        print("✅ tkinterdnd2 已安装")
    except ImportError:
        print("❌ tkinterdnd2 未安装 - 拖放功能不可用")
    
    # 运行测试
    test_invoice_extraction()
    test_csv_functionality()
    
    print("\n" + "=" * 50)
    print("🎉 功能测试完成！")
    print("现在可以启动完整的GUI程序进行测试:")
    print("  python invoice_merger_v5.py")
    print("  或双击: 运行v5.bat")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试过程出错: {e}")
    finally:
        input("\n按回车键退出...")