# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个**发票合并工具**，用于将PDF发票与购买/支付记录图片合并成单个PDF文件。目前版本为 v5.0 稳定版，具有智能数据提取和文件命名功能。

**原创作者**: ZhangStudyLife
**当前版本**: v5.0 智能数据提取版

## 核心架构

### 主要组件

1. **GUI界面层** (`invoice_merger_v5_stable.py`)
   - 基于 tkinter 的图形用户界面
   - 支持文件拖放功能（tkinterdnd2）
   - 实时数据显示和状态反馈
   - 线程化的数据提取处理

2. **PDF合并引擎** (`merge_invoices_simple.py`)
   - 智能布局算法：自动测试8种旋转组合，选择最优布局
   - A4纵向页面，15mm边距，300 DPI渲染
   - 支持水平布局（发票上，记录下）和垂直布局（发票左，记录右）
   - 等比缩放，确保内容不变形

3. **数据提取模块** (内嵌在 `invoice_merger_v5_stable.py`)
   - 使用 pypdfium2 提取PDF文本
   - 正则表达式模式匹配：发票号、日期、金额、销售方
   - 智能文件命名：`日期_金额_发票号后4位_已合并.pdf`
   - CSV汇总记录：持续记录所有处理过的发票

### 版本演进

- **v1.0-v2.0**: 命令行版本，基于文件名匹配
- **v3.0**: GUI版本，手动选择文件
- **v4.0**: 拖放版本，支持文件拖拽
- **v5.0**: 智能版本，新增数据提取和智能命名

## 常用命令

### 开发环境设置

```bash
# 安装运行时依赖
pip install -r requirements.txt

# 安装打包依赖（如需打包）
pip install -r requirements-build.txt
```

### 运行程序

```bash
# 运行 v5.0 稳定版（推荐）
python invoice_merger_v5_stable.py

# 运行 v5.0 完整版
python invoice_merger_v5.py

# 运行测试
python test_v5_functions.py
python test_naming_rules.py
```

### 打包可执行文件

```bash
# 使用专用打包脚本（推荐）
python build_stable_exe.py

# 手动使用 PyInstaller
pyinstaller --onefile --windowed --name=发票合并工具v5稳定版 invoice_merger_v5_stable.py
```

## 关键技术细节

### 智能布局算法

位置: `merge_invoices_simple.py:71-154`

该算法会测试所有图片的旋转组合（2³=8种可能），对每种组合评估两种布局方案：
- **水平布局**: 发票占上部，两张记录图根据宽高比分配下部空间
- **垂直布局**: 发票占左侧，两张记录图纵向排列占右侧

最终选择空间利用率最高的方案（通过缩放因子总和评分）。

### 数据提取流程

位置: `invoice_merger_v5_stable.py:405-455`

1. 使用 pypdfium2 渲染PDF前3页为文本
2. 使用多个正则表达式模式匹配关键信息：
   - 发票号码: `发票号码[：:\s]*(\d{8,20})`
   - 开票日期: `开票日期[：:\s]*(\d{4}[-年]\d{1,2}[-月]\d{1,2}日?)`
   - 金额: `价税合计[：:\s]*¥?(\d+\.?\d*)`
   - 销售方: `销售方[：:\s]*([^\n\r]+?)(?:\s|纳税人)`
3. 日期格式标准化：`年/月/日` → `-`
4. 如果提取失败，使用"未识别"标记，不影响合并功能

### CSV记录格式

位置: `invoice_merger_v5_stable.py:99-108, 667-682`

- 文件名: `发票汇总记录.csv`
- 编码: UTF-8 with BOM (Excel兼容)
- 列: 发票号码 | 开票日期 | 金额 | 销售方名称 | 原文件名 | 合并文件名 | 处理时间

### 文件路径处理

位置: `invoice_merger_v5_stable.py:88-97`

程序会根据运行方式自动检测路径：
- 打包为exe时: 使用 `sys.executable` 的目录
- 源码运行时: 使用 `__file__` 的目录

这确保CSV文件始终保存在正确的位置。

## 依赖说明

### 运行时依赖
- **PyPDF2** (3.0.1): PDF基础操作（已部分替代）
- **Pillow** (10.4.0): 图片处理和合成
- **pypdfium2** (4.30.0): PDF文本提取和高质量渲染
- **tkinterdnd2**: 拖放功能支持（可选，缺失时回退到按钮选择）

### 打包依赖
- **PyInstaller**: 打包为Windows可执行文件

## 打包注意事项

### 使用 build_stable_exe.py

该脚本会自动处理：
1. 检查并安装缺失的依赖
2. 配置正确的 PyInstaller 参数
3. 添加隐式导入（PIL._tkinter_finder, pypdfium2等）
4. 创建发布包目录
5. 生成使用说明文件
6. 清理临时文件

### PyInstaller 关键参数

```bash
--onefile              # 打包为单个exe
--windowed            # 无控制台窗口
--hidden-import       # 确保所有依赖被包含
--add-data            # 包含merge_invoices_simple.py
```

### 常见打包问题

1. **tkinterdnd2缺失**: exe中拖放功能不可用，但不影响基本功能
2. **杀毒软件误报**: 建议用户添加信任
3. **中文路径问题**: 建议放在英文路径下运行

## 测试文件

- `test_v5_functions.py`: 测试v5核心功能
- `test_naming_rules.py`: 测试文件命名规则
- `demo_v5.py`: 演示v5功能
- `demo_product_recognition.py`: 演示商品识别功能
- `test_simplified_products.py`: 测试简化的商品识别

## 已发布版本

发布包位于 `发票合并工具v5稳定版_发布包/` 目录，包含：
- `发票合并工具v5稳定版.exe`: 可执行文件
- `使用说明.md`: 用户使用文档
- `发票汇总记录.csv`: 运行时生成

## 重要注意事项

1. **不修改源文件**: 程序使用临时文件，不会修改原始PDF和图片
2. **CSV持续累积**: 汇总文件会持续记录，不会覆盖
3. **容错设计**: 即使数据提取失败，合并功能仍可正常使用
4. **线程安全**: 数据提取在后台线程，避免界面冻结
5. **编码问题**: 所有文件操作使用UTF-8编码，支持中文路径和文件名（但建议使用英文路径以避免潜在问题）
