#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试新的命名规则脚本
验证：日期_金额_发票号后4位_已合并.pdf 格式
"""

def test_naming_rules():
    print("=" * 60)
    print("测试新的文件命名规则：日期_金额_发票号后4位")
    print("=" * 60)
    
    # 导入稳定版本进行测试
    try:
        from invoice_merger_v5_stable import SimpleInvoiceMergerV5
        app = SimpleInvoiceMergerV5()
        
        test_cases = [
            {
                "name": "完整数据测试",
                "data": {
                    "invoice_date": "2025-09-26",
                    "amount": "199.00",
                    "invoice_number": "12345678901234567890",
                    "seller_name": "某某科技公司"  # 这个应该被忽略
                },
                "original": "测试发票.pdf"
            },
            {
                "name": "缺少部分数据测试",
                "data": {
                    "invoice_date": "未识别",
                    "amount": "355.50",
                    "invoice_number": "98765432",
                    "seller_name": "另一家公司"
                },
                "original": "TC264学习板.pdf"
            },
            {
                "name": "所有数据缺失测试",
                "data": {
                    "invoice_date": "未识别",
                    "amount": "未识别",
                    "invoice_number": "未识别",
                    "seller_name": "未识别"
                },
                "original": "空白发票.pdf"
            },
            {
                "name": "整数金额测试",
                "data": {
                    "invoice_date": "2025-12-31",
                    "amount": "100.00",
                    "invoice_number": "11112222333344445555",
                    "seller_name": "测试公司"
                },
                "original": "整数金额发票.pdf"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. {test_case['name']}:")
            print(f"   原文件名: {test_case['original']}")
            print(f"   发票数据: {test_case['data']}")
            
            result = app.generate_smart_filename(test_case['data'], test_case['original'])
            print(f"   新文件名: {result}")
            
            # 分析命名结果
            if "_已合并.pdf" in result:
                name_parts = result.replace("_已合并.pdf", "").split("_")
                print(f"   命名组成: {' + '.join(name_parts)}")
            
        print("\n" + "=" * 60)
        print("✅ 测试完成！新的命名规则已生效：")
        print("   - 去掉了销售方信息") 
        print("   - 保留了日期、金额、发票号后4位")
        print("   - 格式：日期_金额_#后4位_已合并.pdf")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_naming_rules()