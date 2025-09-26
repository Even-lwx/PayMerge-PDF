#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
发票合并工具 - 智能数据提取版本 v5.0
基于 v4.0 拖放版本升级，新增：
1. 自动提取发票关键数据（发票号、日期、金额、公司信息）
2. 智能重命名合并文件
3. 生成CSV汇总文件，可持续追加发票记录
"""

import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
import sys
import threading
from pathlib import Path
import shutil
import tempfile
import json
import csv
import re
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any

# 导入PDF处理库
try:
    import pypdfium2 as pdfium
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    pdfium = None

# 导入原有的合并逻辑
try:
    from merge_invoices_simple import merge_simple
except ImportError:
    # 如果找不到简化版本，我们稍后会创建它
    pass


class InvoiceDataExtractor:
    """发票数据提取器"""
    
    @staticmethod
    def extract_invoice_data(pdf_path: str) -> Dict[str, Any]:
        """从PDF中提取发票关键信息"""
        if not PDF_AVAILABLE:
            raise ImportError("需要安装pypdfium2库：pip install pypdfium2")
        
        try:
            # 使用pypdfium2提取文本
            doc = pdfium.PdfDocument(pdf_path)
            full_text = ""
            
            for page_num in range(min(3, len(doc))):  # 只处理前3页
                page = doc[page_num]
                textpage = page.get_textpage()
                text = textpage.get_text_range()
                full_text += text + "\n"
                textpage.close()
                page.close()
            
            doc.close()
            
            # 提取关键信息
            data = {
                "file_path": pdf_path,
                "file_name": os.path.basename(pdf_path),
                "extracted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 发票号码 - 多种模式匹配
            invoice_patterns = [
                r'发票号码[：:\s]*(\d{8,20})',
                r'号码[：:\s]*(\d{8,20})',
                r'Invoice\s*No[：:\s]*(\d{8,20})',
                r'(\d{20})',  # 20位数字
                r'(\d{12})',  # 12位数字
            ]
            
            data["invoice_number"] = InvoiceDataExtractor._extract_by_patterns(full_text, invoice_patterns)
                
            # 开票日期
            date_patterns = [
                r'开票日期[：:\s]*(\d{4}[-年]\d{1,2}[-月]\d{1,2}日?)',
                r'日期[：:\s]*(\d{4}[-年]\d{1,2}[-月]\d{1,2}日?)',
                r'(\d{4}[-年]\d{1,2}[-月]\d{1,2}日?)',
                r'(\d{4}/\d{1,2}/\d{1,2})',
            ]
            
            raw_date = InvoiceDataExtractor._extract_by_patterns(full_text, date_patterns)
            if raw_date:
                # 标准化日期格式
                date_str = re.sub(r'年|月', '-', raw_date).replace('日', '').replace('/', '-')
                data["invoice_date"] = date_str
            else:
                data["invoice_date"] = None
                
            # 金额 - 寻找价税合计或总金额
            amount_patterns = [
                r'价税合计[：:\s]*¥?(\d+\.?\d*)',
                r'合计金额[：:\s]*¥?(\d+\.?\d*)',
                r'总计[：:\s]*¥?(\d+\.?\d*)',
                r'金额[：:\s]*¥?(\d+\.?\d*)',
                r'¥(\d+\.?\d*)',
            ]
            
            raw_amount = InvoiceDataExtractor._extract_by_patterns(full_text, amount_patterns)
            if raw_amount:
                try:
                    data["amount"] = float(raw_amount)
                except ValueError:
                    data["amount"] = None
            else:
                data["amount"] = None
                
            # 销售方名称
            seller_patterns = [
                r'销售方[：:\s]*([^\n\r]+?)(?:\s|纳税人|地址|电话)',
                r'卖方[：:\s]*([^\n\r]+?)(?:\s|纳税人|地址|电话)', 
                r'开票单位[：:\s]*([^\n\r]+?)(?:\s|纳税人|地址|电话)',
            ]
            
            seller_name = InvoiceDataExtractor._extract_by_patterns(full_text, seller_patterns)
            if seller_name and len(seller_name.strip()) > 3:
                data["seller_name"] = seller_name.strip()
            else:
                data["seller_name"] = None
                
            # 纳税人识别号
            tax_id_patterns = [
                r'纳税人识别号[：:\s]*([A-Z0-9]{15,20})',
                r'税号[：:\s]*([A-Z0-9]{15,20})',
                r'识别号[：:\s]*([A-Z0-9]{15,20})',
                r'统一社会信用代码[：:\s]*([A-Z0-9]{15,20})',
            ]
            
            data["seller_tax_id"] = InvoiceDataExtractor._extract_by_patterns(full_text, tax_id_patterns)
            
            return data
            
        except Exception as e:
            raise Exception(f"PDF文本提取失败: {str(e)}")
    
    @staticmethod
    def _extract_by_patterns(text: str, patterns: List[str]) -> Optional[str]:
        """使用多个正则模式提取文本"""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None


class CSVManager:
    """CSV汇总文件管理器"""
    
    def __init__(self, csv_file_path: str):
        self.csv_file_path = csv_file_path
        self.ensure_csv_headers()
    
    def ensure_csv_headers(self):
        """确保CSV文件存在且有正确的表头"""
        if not os.path.exists(self.csv_file_path):
            headers = [
                '发票号码', '开票日期', '金额', '销售方名称', '纳税人识别号', 
                '原文件名', '合并文件名', '处理时间'
            ]
            with open(self.csv_file_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
    
    def append_invoice_record(self, invoice_data: Dict[str, Any], merged_filename: str):
        """追加发票记录到CSV文件"""
        try:
            with open(self.csv_file_path, 'a', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    invoice_data.get('invoice_number', ''),
                    invoice_data.get('invoice_date', ''),
                    invoice_data.get('amount', ''),
                    invoice_data.get('seller_name', ''),
                    invoice_data.get('seller_tax_id', ''),
                    invoice_data.get('file_name', ''),
                    merged_filename,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ])
        except Exception as e:
            raise Exception(f"写入CSV文件失败: {str(e)}")


class SmartFileNamer:
    """智能文件命名器"""
    
    @staticmethod
    def generate_smart_filename(invoice_data: Dict[str, Any], original_filename: str) -> str:
        """根据发票数据生成智能文件名"""
        # 获取原文件名（不含扩展名）
        base_name = os.path.splitext(original_filename)[0]
        
        # 构建新文件名组件
        parts = []
        
        # 添加日期
        if invoice_data.get('invoice_date'):
            try:
                date_str = invoice_data['invoice_date'].replace('-', '')
                parts.append(date_str)
            except:
                pass
        
        # 添加金额
        if invoice_data.get('amount'):
            amount_str = f"{invoice_data['amount']:.2f}元".replace('.00元', '元')
            parts.append(amount_str)
        
        # 添加发票号后4位
        if invoice_data.get('invoice_number') and len(str(invoice_data['invoice_number'])) >= 4:
            last4 = str(invoice_data['invoice_number'])[-4:]
            parts.append(f"#{last4}")
        
        # 组合文件名
        if parts:
            smart_name = '_'.join(parts) + '_已合并'
        else:
            # 如果没有提取到数据，使用原名称
            smart_name = base_name + '_已合并'
        
        return smart_name + '.pdf'


class DragDropInvoiceMergerV5:
    """v5.0 智能发票合并工具"""
    
    def __init__(self):
        self.root = TkinterDnD.Tk()
        self.root.title("发票合并工具 v5.0 - 智能数据提取版")
        self.root.geometry("900x800")
        self.root.resizable(True, True)

        # 文件存储
        self.pdf_file = None
        self.image_files = []
        
        # 数据提取结果
        self.extracted_data = None
        
        # CSV管理器
        self.csv_manager = None
        self.csv_path = None

        # 颜色主题
        self.colors = {
            'bg': '#f5f5f5',
            'drop_zone': '#e8f4fd',
            'drop_zone_active': '#c3e7fd',
            'button': '#4a90e2',
            'button_hover': '#357abd',
            'success': '#52c41a',
            'error': '#f5222d',
            'warning': '#fa8c16',
            'text': '#333333',
            'data_bg': '#f6ffed',
            'data_border': '#b7eb8f'
        }

        self.init_csv_file()  # 先初始化CSV文件
        self.setup_ui()

    def init_csv_file(self):
        """初始化CSV汇总文件"""
        # CSV文件放在程序所在目录
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
            
        self.csv_path = os.path.join(app_dir, "发票汇总记录.csv")
        self.csv_manager = CSVManager(self.csv_path)

    def setup_ui(self):
        self.root.configure(bg=self.colors['bg'])

        # 主标题
        title_frame = tk.Frame(self.root, bg=self.colors['bg'])
        title_frame.pack(fill=tk.X, padx=20, pady=(15, 5))
        
        title_label = tk.Label(
            title_frame,
            text="📄 发票合并工具 v5.0 - 智能数据提取版",
            font=("微软雅黑", 18, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        title_label.pack()

        # 功能说明
        info_label = tk.Label(
            self.root,
            text="🎯 拖放文件：1个PDF发票 + 2张图片 → 🔍 智能命名：日期_金额_发票号 → 📊 生成汇总记录",
            font=("微软雅黑", 11),
            bg=self.colors['bg'],
            fg='#666666'
        )
        info_label.pack(pady=(0, 15))

        # 主容器
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # 拖放区域
        self.setup_drop_zone(main_frame)
        
        # 文件列表
        self.setup_file_list(main_frame)
        
        # 数据显示区域
        self.setup_data_display(main_frame)
        
        # 按钮区域
        self.setup_buttons(main_frame)
        
        # 状态栏
        self.setup_status_bar(main_frame)

        # 配置拖放功能
        self.setup_drag_drop()

    def setup_drop_zone(self, parent):
        """设置拖放区域"""
        self.drop_zone = tk.Frame(
            parent,
            bg=self.colors['drop_zone'],
            relief=tk.RIDGE,
            borderwidth=3,
            height=120
        )
        self.drop_zone.pack(fill=tk.X, pady=(0, 10))

        self.drop_label = tk.Label(
            self.drop_zone,
            text="🎯 将文件拖放到这里\n支持格式：PDF、JPG、PNG",
            font=("微软雅黑", 14),
            bg=self.colors['drop_zone'],
            fg='#666666'
        )
        self.drop_label.pack(expand=True)

    def setup_file_list(self, parent):
        """设置文件列表区域"""
        files_frame = tk.LabelFrame(
            parent,
            text="📁 已选择的文件",
            font=("微软雅黑", 11, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        files_frame.pack(fill=tk.X, pady=(0, 10))

        self.file_listbox = tk.Listbox(
            files_frame,
            height=3,
            font=("微软雅黑", 10),
            selectmode=tk.SINGLE,
            bg='white'
        )
        self.file_listbox.pack(fill=tk.X, padx=10, pady=5)

    def setup_data_display(self, parent):
        """设置数据显示区域"""
        data_frame = tk.LabelFrame(
            parent,
            text="🔍 提取的发票数据",
            font=("微软雅黑", 11, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        data_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 创建Notebook来分页显示
        notebook = ttk.Notebook(data_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 数据预览页
        preview_frame = tk.Frame(notebook, bg='white')
        notebook.add(preview_frame, text="📊 数据预览")
        
        self.data_text = tk.Text(
            preview_frame,
            height=8,
            font=("Consolas", 10),
            bg=self.colors['data_bg'],
            fg=self.colors['text'],
            state=tk.DISABLED,
            wrap=tk.WORD
        )
        self.data_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 文件命名预览页
        naming_frame = tk.Frame(notebook, bg='white')
        notebook.add(naming_frame, text="📝 文件命名")
        
        self.naming_text = tk.Text(
            naming_frame,
            height=4,
            font=("微软雅黑", 10),
            bg='#fff7e6',
            fg=self.colors['text'],
            state=tk.DISABLED,
            wrap=tk.WORD
        )
        self.naming_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def setup_buttons(self, parent):
        """设置按钮区域"""
        button_frame = tk.Frame(parent, bg=self.colors['bg'])
        button_frame.pack(fill=tk.X, pady=(0, 10))

        # 左侧按钮
        left_buttons = tk.Frame(button_frame, bg=self.colors['bg'])
        left_buttons.pack(side=tk.LEFT)
        
        self.clear_btn = tk.Button(
            left_buttons,
            text="🗑️ 清除",
            font=("微软雅黑", 10),
            bg='#ff7875',
            fg='white',
            padx=15,
            pady=8,
            relief=tk.FLAT,
            command=self.clear_files
        )
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.select_btn = tk.Button(
            left_buttons,
            text="📁 选择文件",
            font=("微软雅黑", 10),
            bg='#52c41a',
            fg='white',
            padx=15,
            pady=8,
            relief=tk.FLAT,
            command=self.select_files
        )
        self.select_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 右侧按钮
        right_buttons = tk.Frame(button_frame, bg=self.colors['bg'])
        right_buttons.pack(side=tk.RIGHT)
        
        self.extract_btn = tk.Button(
            right_buttons,
            text="🔍 提取数据",
            font=("微软雅黑", 10),
            bg=self.colors['warning'],
            fg='white',
            padx=15,
            pady=8,
            relief=tk.FLAT,
            command=self.extract_data_thread,
            state=tk.DISABLED
        )
        self.extract_btn.pack(side=tk.RIGHT, padx=(10, 0))

        self.merge_btn = tk.Button(
            right_buttons,
            text="🚀 智能合并",
            font=("微软雅黑", 11, "bold"),
            bg=self.colors['button'],
            fg='white',
            padx=20,
            pady=8,
            relief=tk.FLAT,
            command=self.merge_files_thread,
            state=tk.DISABLED
        )
        self.merge_btn.pack(side=tk.RIGHT, padx=(10, 0))

    def setup_status_bar(self, parent):
        """设置状态栏"""
        status_frame = tk.Frame(parent, bg=self.colors['bg'])
        status_frame.pack(fill=tk.X)
        
        self.status_label = tk.Label(
            status_frame,
            text="请拖放或选择文件开始操作",
            font=("微软雅黑", 10),
            bg=self.colors['bg'],
            fg='#666666'
        )
        self.status_label.pack(side=tk.LEFT)
        
        # CSV文件信息
        if self.csv_path:
            csv_filename = os.path.basename(self.csv_path)
        else:
            csv_filename = "发票汇总记录.csv"
            
        csv_info = tk.Label(
            status_frame,
            text=f"📊 汇总文件: {csv_filename}",
            font=("微软雅黑", 9),
            bg=self.colors['bg'],
            fg='#999999'
        )
        csv_info.pack(side=tk.RIGHT)

    def setup_drag_drop(self):
        """设置拖放功能"""
        self.drop_zone.drop_target_register(DND_FILES)
        self.drop_zone.dnd_bind('<<DropEnter>>', self.on_drop_enter)
        self.drop_zone.dnd_bind('<<DropLeave>>', self.on_drop_leave)
        self.drop_zone.dnd_bind('<<Drop>>', self.on_drop)

    def on_drop_enter(self, event):
        self.drop_zone.config(bg=self.colors['drop_zone_active'])

    def on_drop_leave(self, event):
        self.drop_zone.config(bg=self.colors['drop_zone'])

    def on_drop(self, event):
        self.drop_zone.config(bg=self.colors['drop_zone'])
        files = self.root.tk.splitlist(event.data)
        self.add_files(files)

    def add_files(self, file_paths: List[str]):
        """添加文件"""
        for file_path in file_paths:
            file_path = file_path.strip().strip('"')
            if not os.path.exists(file_path):
                continue

            ext = os.path.splitext(file_path)[1].lower()

            if ext == '.pdf':
                if self.pdf_file:
                    if messagebox.askyesno("替换PDF", "已有PDF文件，是否替换？"):
                        self.pdf_file = file_path
                else:
                    self.pdf_file = file_path

            elif ext in ['.jpg', '.jpeg', '.png']:
                if len(self.image_files) >= 2:
                    if messagebox.askyesno("替换图片", "已有2张图片，是否替换最早的一张？"):
                        self.image_files.pop(0)
                        self.image_files.append(file_path)
                else:
                    self.image_files.append(file_path)
            else:
                self.status_label.config(text=f"不支持的文件格式: {ext}")
                continue

        self.update_file_list()
        
        # 如果有PDF文件，自动提取数据
        if self.pdf_file and PDF_AVAILABLE:
            self.extract_data_thread()

    def select_files(self):
        """通过对话框选择文件"""
        files = filedialog.askopenfilenames(
            title="选择文件",
            filetypes=[
                ("所有支持的文件", "*.pdf;*.jpg;*.jpeg;*.png"),
                ("PDF文件", "*.pdf"),
                ("图片文件", "*.jpg;*.jpeg;*.png"),
                ("所有文件", "*.*")
            ]
        )
        if files:
            self.add_files(list(files))

    def clear_files(self):
        """清除所有文件"""
        self.pdf_file = None
        self.image_files = []
        self.extracted_data = None
        self.update_file_list()
        self.update_displays()

    def update_file_list(self):
        """更新文件列表显示"""
        self.file_listbox.delete(0, tk.END)

        if self.pdf_file:
            self.file_listbox.insert(tk.END, f"📄 PDF: {os.path.basename(self.pdf_file)}")

        for i, img_file in enumerate(self.image_files, 1):
            self.file_listbox.insert(tk.END, f"🖼️ 图片{i}: {os.path.basename(img_file)}")

        self.update_button_states()

    def update_button_states(self):
        """更新按钮状态"""
        # 提取数据按钮
        if self.pdf_file and PDF_AVAILABLE:
            self.extract_btn.config(state=tk.NORMAL)
        else:
            self.extract_btn.config(state=tk.DISABLED)

        # 合并按钮
        if self.pdf_file and len(self.image_files) == 2:
            self.merge_btn.config(state=tk.NORMAL)
            self.status_label.config(text="✅ 文件已就绪，可以合并")
        else:
            self.merge_btn.config(state=tk.DISABLED)
            if not self.pdf_file:
                self.status_label.config(text="请选择PDF文件")
            elif len(self.image_files) != 2:
                self.status_label.config(text=f"需要2张图片，当前有{len(self.image_files)}张")

    def extract_data_thread(self):
        """在线程中提取数据"""
        if not self.pdf_file or not PDF_AVAILABLE:
            return
            
        self.extract_btn.config(state=tk.DISABLED, text="🔄 提取中...")
        self.status_label.config(text="正在提取发票数据，请稍候...")
        
        def extract_worker():
            try:
                self.extracted_data = InvoiceDataExtractor.extract_invoice_data(self.pdf_file)
                self.root.after(0, self.extract_success)
            except Exception as e:
                self.root.after(0, self.extract_failed, str(e))
        
        thread = threading.Thread(target=extract_worker, daemon=True)
        thread.start()

    def extract_success(self):
        """数据提取成功"""
        self.extract_btn.config(state=tk.NORMAL, text="🔍 提取数据")
        self.status_label.config(text="✅ 数据提取成功！")
        self.update_displays()

    def extract_failed(self, error_msg):
        """数据提取失败"""
        self.extract_btn.config(state=tk.NORMAL, text="🔍 提取数据")
        self.status_label.config(text="❌ 数据提取失败")
        messagebox.showwarning("数据提取失败", f"提取过程中出现问题：\n{error_msg}\n\n将使用原文件名进行合并")

    def update_displays(self):
        """更新数据显示和文件命名预览"""
        # 更新数据显示
        self.data_text.config(state=tk.NORMAL)
        self.data_text.delete(1.0, tk.END)
        
        if self.extracted_data:
            display_text = "🔍 发票数据提取结果：\n"
            display_text += "=" * 50 + "\n\n"
            
            items = [
                ("📄 文件名", self.extracted_data.get("file_name", "未知")),
                ("🔢 发票号码", self.extracted_data.get("invoice_number", "未识别")),
                ("📅 开票日期", self.extracted_data.get("invoice_date", "未识别")),
                ("💰 金额", f"¥{self.extracted_data.get('amount', 0):.2f}" if self.extracted_data.get('amount') else "未识别"),
                ("🏢 销售方", self.extracted_data.get("seller_name", "未识别")),
                ("🆔 纳税人识别号", self.extracted_data.get("seller_tax_id", "未识别")),
                ("⏰ 提取时间", self.extracted_data.get("extracted_at", ""))
            ]
            
            for label, value in items:
                display_text += f"{label}: {value}\n"
            
        else:
            display_text = "💡 提示：选择PDF文件后点击【提取数据】按钮\n\n"
            display_text += "✨ 功能特色：\n"
            display_text += "• 智能识别发票号码、日期、金额\n"
            display_text += "• 自动提取企业信息\n"
            display_text += "• 生成智能文件名\n"
            display_text += "• 持续汇总到CSV文件"
        
        self.data_text.insert(1.0, display_text)
        self.data_text.config(state=tk.DISABLED)
        
        # 更新文件命名预览
        self.naming_text.config(state=tk.NORMAL)
        self.naming_text.delete(1.0, tk.END)
        
        if self.pdf_file:
            original_name = os.path.basename(self.pdf_file)
            if self.extracted_data:
                smart_name = SmartFileNamer.generate_smart_filename(self.extracted_data, original_name)
                naming_text = f"📝 智能重命名预览：\n\n"
                naming_text += f"原文件名：{original_name}\n"
                naming_text += f"新文件名：{smart_name}\n\n"
                naming_text += "💡 命名规则：日期_销售方_金额_发票号后4位"
            else:
                base_name = os.path.splitext(original_name)[0]
                default_name = base_name + "_已合并.pdf"
                naming_text = f"📝 默认命名：\n\n"
                naming_text += f"原文件名：{original_name}\n"
                naming_text += f"合并文件名：{default_name}\n\n"
                naming_text += "💡 提取数据后将启用智能命名"
        else:
            naming_text = "💡 选择PDF文件后将显示命名预览"
            
        self.naming_text.insert(1.0, naming_text)
        self.naming_text.config(state=tk.DISABLED)

    def merge_files_thread(self):
        """在线程中处理合并"""
        if not (self.pdf_file and len(self.image_files) == 2):
            messagebox.showerror("文件不完整", "需要1个PDF文件和2张图片才能合并")
            return

        self.merge_btn.config(state=tk.DISABLED, text="🔄 处理中...")
        self.status_label.config(text="正在智能合并文件...")

        def merge_worker():
            try:
                # 生成智能文件名
                original_filename = os.path.basename(self.pdf_file)
                if self.extracted_data:
                    smart_filename = SmartFileNamer.generate_smart_filename(self.extracted_data, original_filename)
                else:
                    base_name = os.path.splitext(original_filename)[0]
                    smart_filename = base_name + "_已合并.pdf"

                # 弹出保存对话框
                output_path = filedialog.asksaveasfilename(
                    title="保存合并后的PDF",
                    defaultextension=".pdf",
                    initialfile=smart_filename,
                    filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
                )

                if not output_path:
                    self.root.after(0, self.merge_cancelled)
                    return

                # 创建临时文件
                temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
                temp_buy = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)  
                temp_pay = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                
                temp_pdf.close()
                temp_buy.close()
                temp_pay.close()

                # 复制文件到临时位置
                shutil.copy2(self.pdf_file, temp_pdf.name)
                
                # 复制图片文件（按文件名排序）
                sorted_images = sorted(self.image_files, key=lambda x: os.path.basename(x).lower())
                for i, img_file in enumerate(sorted_images):
                    target = temp_buy.name if i == 0 else temp_pay.name
                    shutil.copy2(img_file, target)

                # 调用合并函数
                from merge_invoices_simple import merge_simple
                merge_simple(temp_pdf.name, temp_buy.name, temp_pay.name, output_path)

                # 记录到CSV文件
                if self.extracted_data:
                    merged_filename = os.path.basename(output_path)
                    self.csv_manager.append_invoice_record(self.extracted_data, merged_filename)

                # 清理临时文件
                for temp_file in [temp_pdf.name, temp_buy.name, temp_pay.name]:
                    try:
                        os.unlink(temp_file)
                    except:
                        pass

                self.root.after(0, self.merge_success, output_path, smart_filename)

            except Exception as e:
                self.root.after(0, self.merge_failed, str(e))

        thread = threading.Thread(target=merge_worker, daemon=True)
        thread.start()

    def merge_cancelled(self):
        """合并取消"""
        self.merge_btn.config(state=tk.NORMAL, text="🚀 智能合并")
        self.status_label.config(text="合并已取消")

    def merge_success(self, output_path: str, smart_filename: str):
        """合并成功"""
        self.merge_btn.config(state=tk.NORMAL, text="🚀 智能合并")
        self.status_label.config(text="✅ 合并成功！已更新汇总记录")

        # 构建成功消息
        message = f"文件已保存到：\n{output_path}\n\n"
        if self.extracted_data:
            message += "🔍 已提取发票数据\n"
            message += "📝 使用智能文件名\n"
            if self.csv_path:
                message += f"📊 已记录到汇总文件：{os.path.basename(self.csv_path)}\n\n"
        
        message += "是否打开文件所在目录？"

        result = messagebox.askyesno("合并成功", message)

        if result:
            output_dir = os.path.dirname(output_path)
            if sys.platform == 'win32':
                os.startfile(output_dir)
            elif sys.platform == 'darwin':
                os.system(f'open "{output_dir}"')
            else:
                os.system(f'xdg-open "{output_dir}"')

        # 询问是否继续
        if messagebox.askyesno("继续", "是否继续处理其他发票？"):
            self.clear_files()

    def merge_failed(self, error_msg: str):
        """合并失败"""
        self.merge_btn.config(state=tk.NORMAL, text="🚀 智能合并")
        self.status_label.config(text="❌ 合并失败")
        messagebox.showerror("合并失败", f"合并过程中出现错误：\n{error_msg}")

    def run(self):
        """运行主程序"""
        # 居中显示窗口
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        # 确保所有组件都已初始化后再更新显示
        self.root.after(100, self.update_displays)

        self.root.mainloop()


def main():
    """主入口"""
    try:
        if not PDF_AVAILABLE:
            messagebox.showwarning(
                "缺少依赖",
                "未检测到pypdfium2库，数据提取功能将不可用。\n\n"
                "安装方法：pip install pypdfium2\n\n"
                "您仍可使用基础的文件合并功能。"
            )
            
        app = DragDropInvoiceMergerV5()
        app.run()
        return 0
        
    except ImportError as e:
        if "tkinterdnd2" in str(e):
            messagebox.showerror(
                "缺少依赖",
                "需要安装tkinterdnd2库才能使用拖放功能。\n\n"
                "请运行以下命令安装：\n"
                "pip install tkinterdnd2"
            )
        else:
            messagebox.showerror("错误", f"程序启动失败：\n{e}")
        return 1
    except Exception as e:
        messagebox.showerror("错误", f"程序启动失败：\n{e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())