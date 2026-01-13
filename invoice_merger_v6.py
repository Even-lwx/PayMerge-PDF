#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ASC实验室发票合并工具 v6.1 - 李文轩天才杰作~
基于 v4.0 拖放版本升级，新增智能数据提取功能
简化版本，专注于稳定性和可靠性
"""

import tkinter as tk
from tkinter import messagebox, filedialog, ttk
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

# 尝试导入拖放功能库
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DRAG_DROP_AVAILABLE = True
except ImportError:
    DRAG_DROP_AVAILABLE = False
    # 使用普通的Tk作为备选
    TkinterDnD = tk

# 尝试导入PDF处理库
try:
    import pypdfium2 as pdfium
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    pdfium = None

# 尝试导入Excel处理库
try:
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    openpyxl = None

# 导入v6合并逻辑
try:
    from merge_invoices_v6 import merge_with_multi_pages, merge_simple
except ImportError:
    try:
        from merge_invoices_simple import merge_simple
        merge_with_multi_pages = None
    except ImportError:
        def merge_simple(pdf_path, img1_path, img2_path, output_path):
            raise ImportError("找不到合并功能模块")
        merge_with_multi_pages = None


class ConfigManager:
    """配置管理器"""
    def __init__(self):
        self.config_path = self.get_config_path()
        self.config = self.load_config()
    
    def get_config_path(self):
        try:
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.abspath(__file__))
            return os.path.join(app_dir, "config.json")
        except:
            return "config.json"
    
    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_config(self, config):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            self.config = config
            return True
        except:
            return False
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value
        return self.save_config(self.config)
    
    def is_first_run(self):
        return not self.config.get('name') or not self.config.get('group')


class ConfigDialog(tk.Toplevel):
    """配置对话框 - 美化版"""
    def __init__(self, parent, title="配置信息", initial_name="", initial_group="", initial_output_path=""):
        super().__init__(parent)
        self.title(title)
        self.geometry("480x620")
        self.resizable(False, False)
        self.result = None
        self.name_var = tk.StringVar(value=initial_name)
        self.group_var = tk.StringVar(value=initial_group)
        self.initial_output_path = initial_output_path
        
        # 设置背景色
        self.configure(bg='#f0f4f8')
        
        self.setup_ui()
        
        # 确保对话框显示在最前面
        self.transient(parent)
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        # 强制显示并置顶
        self.lift()
        self.focus_force()
        self.grab_set()
    
    def setup_ui(self):
        # 主容器 - 模拟卡片效果
        main_card = tk.Frame(self, bg='white', highlightbackground='#e0e0e0', highlightthickness=1)
        main_card.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        # 顶部装饰条
        header_bar = tk.Frame(main_card, bg='#4a90e2', height=8)
        header_bar.pack(fill=tk.X)
        header_bar.pack_propagate(False)
        
        # 标题区域
        title_frame = tk.Frame(main_card, bg='white')
        title_frame.pack(fill=tk.X, pady=(20, 15))
        
        # 图标 + 标题
        tk.Label(title_frame, text="👤", font=("Segoe UI Emoji", 28), bg='white').pack()
        tk.Label(title_frame, text="请输入使用者信息", font=("微软雅黑", 18, "bold"), fg="#2c3e50", bg='white').pack(pady=(8, 0))
        tk.Label(title_frame, text="此信息将用于记录操作日志", font=("微软雅黑", 10), fg="#7f8c8d", bg='white').pack(pady=(5, 0))
        
        # 输入区域
        input_frame = tk.Frame(main_card, bg='white')
        input_frame.pack(padx=35, pady=15, fill=tk.X)
        
        # 姓名输入
        tk.Label(input_frame, text="姓名", font=("微软雅黑", 12, "bold"), fg="#34495e", bg='white', anchor='w').pack(fill=tk.X, pady=(0, 5))
        
        name_entry_frame = tk.Frame(input_frame, bg='#e8f4fd', highlightbackground='#4a90e2', highlightthickness=2)
        name_entry_frame.pack(fill=tk.X, pady=(0, 15))
        self.name_entry = tk.Entry(name_entry_frame, textvariable=self.name_var, font=("微软雅黑", 14), 
                                    relief='flat', bg='#e8f4fd', fg='#2c3e50')
        self.name_entry.pack(fill=tk.X, padx=10, pady=10)
        self.name_entry.focus()
        
        # 组别输入
        tk.Label(input_frame, text="组别", font=("微软雅黑", 12, "bold"), fg="#34495e", bg='white', anchor='w').pack(fill=tk.X, pady=(0, 5))
        
        group_entry_frame = tk.Frame(input_frame, bg='#e8f4fd', highlightbackground='#4a90e2', highlightthickness=2)
        group_entry_frame.pack(fill=tk.X)
        self.group_entry = tk.Entry(group_entry_frame, textvariable=self.group_var, font=("微软雅黑", 14), 
                                     relief='flat', bg='#e8f4fd', fg='#2c3e50')
        self.group_entry.pack(fill=tk.X, padx=10, pady=10)
        
        # 输出路径配置
        tk.Label(input_frame, text="输出路径（可选）", font=("微软雅黑", 12, "bold"), fg="#34495e", bg='white', anchor='w').pack(fill=tk.X, pady=(15, 5))
        
        output_path_container = tk.Frame(input_frame, bg='white')
        output_path_container.pack(fill=tk.X)
        
        output_entry_frame = tk.Frame(output_path_container, bg='#e8f4fd', highlightbackground='#4a90e2', highlightthickness=2)
        output_entry_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.output_path_var = tk.StringVar(value=getattr(self, 'initial_output_path', ''))
        self.output_path_entry = tk.Entry(output_entry_frame, textvariable=self.output_path_var, font=("微软雅黑", 11), 
                                          relief='flat', bg='#e8f4fd', fg='#2c3e50')
        self.output_path_entry.pack(fill=tk.X, padx=8, pady=8)
        
        browse_btn = tk.Button(output_path_container, text="📁", font=("Segoe UI Emoji", 12),
                               bg='#4a90e2', fg='white', relief='flat', cursor='hand2',
                               command=self.browse_output_path)
        browse_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        tk.Label(input_frame, text="留空则使用软件所在目录", font=("微软雅黑", 9), fg="#95a5a6", bg='white', anchor='w').pack(fill=tk.X, pady=(2, 0))
        
        # 按钮区域
        button_frame = tk.Frame(main_card, bg='white')
        button_frame.pack(pady=25)
        
        # 确定按钮
        ok_btn = tk.Button(button_frame, text="✓ 确  定", font=("微软雅黑", 13, "bold"), 
                          bg="#27ae60", fg="white", activebackground="#2ecc71", activeforeground="white",
                          width=12, height=2, relief='flat', cursor='hand2', command=self.ok)
        ok_btn.pack(side=tk.LEFT, padx=10)
        
        # 取消按钮
        cancel_btn = tk.Button(button_frame, text="✕ 取  消", font=("微软雅黑", 13), 
                              bg="#bdc3c7", fg="#2c3e50", activebackground="#95a5a6", activeforeground="white",
                              width=12, height=2, relief='flat', cursor='hand2', command=self.cancel)
        cancel_btn.pack(side=tk.LEFT, padx=10)
        
        self.bind('<Return>', lambda e: self.ok())
        self.bind('<Escape>', lambda e: self.cancel())
    
    def validate_input(self, text: str, field_name: str) -> tuple:
        """验证输入只包含中文、英文、数字、下划线"""
        import re
        if not text:
            return False, f"{field_name}不能为空"
        # 只允许中文、英文、数字、下划线
        pattern = r'^[\u4e00-\u9fa5a-zA-Z0-9_]+$'
        if not re.match(pattern, text):
            return False, f"{field_name}只能包含中文、英文、数字和下划线"
        return True, ""
    
    def ok(self):
        name = self.name_var.get().strip()
        group = self.group_var.get().strip()
        
        # 验证姓名
        valid, msg = self.validate_input(name, "姓名")
        if not valid:
            messagebox.showwarning("输入错误", msg, parent=self)
            self.name_entry.focus()
            return
        
        # 验证组别
        valid, msg = self.validate_input(group, "组别")
        if not valid:
            messagebox.showwarning("输入错误", msg, parent=self)
            self.group_entry.focus()
            return
        
        # 验证输出路径（如果有）
        if hasattr(self, 'output_path_var'):
            output_path = self.output_path_var.get().strip()
            if output_path:
                # 检查路径是否有效
                if not os.path.isdir(output_path):
                    if not messagebox.askyesno("路径不存在", f"输出路径不存在，是否创建？\n{output_path}", parent=self):
                        return
                    try:
                        os.makedirs(output_path, exist_ok=True)
                    except Exception as e:
                        messagebox.showerror("创建失败", f"无法创建目录：\n{e}", parent=self)
                        return
                self.result = {'name': name, 'group': group, 'output_path': output_path}
            else:
                self.result = {'name': name, 'group': group}
        else:
            self.result = {'name': name, 'group': group}
        self.destroy()
    
    def browse_output_path(self):
        """浏览选择输出路径"""
        current_path = self.output_path_var.get().strip()
        initial_dir = current_path if current_path and os.path.isdir(current_path) else os.path.expanduser('~')
        
        folder = filedialog.askdirectory(title="选择输出目录", initialdir=initial_dir, parent=self)
        if folder:
            self.output_path_var.set(folder)
    
    def cancel(self):
        self.result = None
        self.destroy()


class SimpleInvoiceMergerV6:
    """ ASC实验室发票合并工具 v6.1 - 李文轩天才杰作~"""
    
    def __init__(self):
        # 配置管理器
        self.config_manager = ConfigManager()
        
        # 使用支持的Tk类型
        if DRAG_DROP_AVAILABLE:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()
        
        # 先设置主窗口属性
        self.root.title("ASC实验室发票合并工具 v6.1 - 李文轩天才杰作~")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # 设置窗口图标
        self.set_window_icon()

        # 文件存储
        self.pdf_file = None
        self.image_files = []
        
        # 数据提取结果
        self.extracted_data = None

        # 颜色主题
        self.colors = {
            'bg': '#f5f5f5',
            'drop_zone': '#e8f4fd',
            'drop_zone_active': '#c3e7fd',
            'button': '#4a90e2',
            'success': '#52c41a',
            'error': '#f5222d',
            'warning': '#fa8c16',
            'text': '#333333',
        }

        self.setup_ui()

    def set_window_icon(self):
        """设置窗口图标"""
        try:
            # 获取图标路径
            if getattr(sys, 'frozen', False):
                # 打包后的exe
                base_path = sys._MEIPASS
            else:
                # 开发环境
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            # 尝试加载ico文件
            ico_path = os.path.join(base_path, 'source', 'icon.ico')
            png_path = os.path.join(base_path, 'source', '1.png')
            
            if os.path.exists(ico_path):
                self.root.iconbitmap(ico_path)
            elif os.path.exists(png_path):
                # 如果没有ico，尝试用png
                from PIL import Image, ImageTk
                icon_img = Image.open(png_path)
                icon_photo = ImageTk.PhotoImage(icon_img)
                self.root.iconphoto(True, icon_photo)
                self._icon_photo = icon_photo  # 保持引用防止被垃圾回收
        except Exception as e:
            # 图标加载失败不影响程序运行
            print(f"图标加载失败: {e}")

    def create_rounded_frame(self, parent, bg_color, radius=15, border_color=None, border_width=2):
        """创建带圆角效果的Frame（使用Canvas模拟）"""
        frame = tk.Frame(parent, bg=self.colors['bg'])
        return frame
    
    def create_card_frame(self, parent, title=None, bg='white'):
        """创建卡片式Frame"""
        # 外层容器
        outer = tk.Frame(parent, bg=self.colors['bg'])
        
        # 卡片主体 - 使用浅色背景和边框模拟圆角效果
        card = tk.Frame(outer, bg=bg, highlightbackground='#e0e0e0', highlightthickness=1, padx=2, pady=2)
        card.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        if title:
            title_bar = tk.Frame(card, bg='#4a90e2', height=4)
            title_bar.pack(fill=tk.X)
            title_label = tk.Label(card, text=title, font=("微软雅黑", 11, "bold"), bg=bg, fg='#2c3e50', anchor='w')
            title_label.pack(fill=tk.X, padx=10, pady=(8, 5))
        
        # 内容区域
        content = tk.Frame(card, bg=bg)
        content.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        return outer, content

    def show_config_dialog(self, is_first_run=False):
        """显示配置对话框"""
        if is_first_run:
            title = "首次运行 - 配置信息"
            initial_name = ""
            initial_group = ""
            initial_output_path = ""
        else:
            title = "修改配置"
            initial_name = self.config_manager.get('name', '')
            initial_group = self.config_manager.get('group', '')
            initial_output_path = self.config_manager.get('output_path_absolute', '')
        
        dialog = ConfigDialog(self.root, title, initial_name, initial_group, initial_output_path)
        self.root.wait_window(dialog)
        
        if dialog.result:
            self.config_manager.set('name', dialog.result['name'])
            self.config_manager.set('group', dialog.result['group'])
            
            # 保存输出路径（同时保存绝对路径和相对路径）
            if 'output_path' in dialog.result and dialog.result['output_path']:
                output_path = dialog.result['output_path']
                self.config_manager.set('output_path_absolute', os.path.abspath(output_path))
                # 计算相对路径（相对于程序目录）
                try:
                    if getattr(sys, 'frozen', False):
                        app_dir = os.path.dirname(sys.executable)
                    else:
                        app_dir = os.path.dirname(os.path.abspath(__file__))
                    rel_path = os.path.relpath(output_path, app_dir)
                    self.config_manager.set('output_path_relative', rel_path)
                except ValueError:
                    # 不同盘符无法计算相对路径
                    self.config_manager.set('output_path_relative', '')
            else:
                self.config_manager.set('output_path_absolute', '')
                self.config_manager.set('output_path_relative', '')
            
            if hasattr(self, 'config_label'):
                self.update_config_display()
            return True
        return False

    def update_config_display(self):
        """更新配置显示"""
        name = self.config_manager.get('name', '未配置')
        group = self.config_manager.get('group', '未配置')
        output_path = self.config_manager.get('output_path_absolute', '')
        if output_path:
            # 显示路径的简短版本
            if len(output_path) > 30:
                display_path = "..." + output_path[-27:]
            else:
                display_path = output_path
            self.config_label.config(text=f"👤 {name}  |  📊 {group}  |  📁 {display_path}")
        else:
            self.config_label.config(text=f"👤 使用者：{name}  |  📊 组别：{group}")
    
    def get_output_directory(self) -> tuple:
        """
        获取有效的输出目录
        返回: (output_dir, error_message)
        优先使用绝对路径，失败则尝试相对路径，都失败则返回错误
        """
        # 获取程序根目录（作为默认和相对路径基准）
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 获取配置的路径
        abs_path = self.config_manager.get('output_path_absolute', '')
        rel_path = self.config_manager.get('output_path_relative', '')
        
        # 如果没有配置路径，使用程序根目录
        if not abs_path and not rel_path:
            return app_dir, None
        
        # 优先尝试绝对路径
        if abs_path and os.path.isdir(abs_path):
            return abs_path, None
        
        # 尝试相对路径
        if rel_path:
            full_rel_path = os.path.join(app_dir, rel_path)
            if os.path.isdir(full_rel_path):
                return full_rel_path, None
        
        # 两个路径都无效
        error_msg = f"配置的输出路径无效！\\n\\n绝对路径：{abs_path or '(未设置)'}\\n相对路径：{rel_path or '(未设置)'}\\n\\n请点击【修改配置】重新设置输出路径。"
        return None, error_msg

    def setup_ui(self):
        self.root.configure(bg=self.colors['bg'])

        # 标题
        title_label = tk.Label(
            self.root,
            text="📄ASC实验室发票合并工具 v6.1 - 李文轩天才杰作~",
            font=("微软雅黑", 16, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        title_label.pack(pady=(20, 5))

        # 配置信息显示和修改按钮
        config_frame = tk.Frame(self.root, bg=self.colors['bg'])
        config_frame.pack(pady=(0, 10))
        
        self.config_label = tk.Label(
            config_frame,
            text="",
            font=("微软雅黑", 10),
            bg=self.colors['bg'],
            fg='#666666'
        )
        self.config_label.pack(side=tk.LEFT, padx=(0, 10))
        self.update_config_display()
        
        tk.Button(
            config_frame,
            text="⚙️ 修改配置",
            font=("微软雅黑", 9),
            bg='#d9d9d9',
            fg='#333333',
            command=lambda: self.show_config_dialog(is_first_run=False)
        ).pack(side=tk.LEFT)

        # 功能说明
        info_text = "🎯 拖放或选择文件：1个PDF发票（支持多页） + 2张图片（按顺序：购买记录、支付记录）"
        info_label = tk.Label(
            self.root,
            text=info_text,
            font=("微软雅黑", 10),
            bg=self.colors['bg'],
            fg='#666666'
        )
        info_label.pack(pady=(0, 15))

        # 主容器
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # 拖放区域或文件选择区域
        self.setup_file_area(main_frame)
        
        # 文件列表
        self.setup_file_list(main_frame)
        
        # 数据显示区域
        self.setup_data_display(main_frame)
        
        # 按钮区域
        self.setup_buttons(main_frame)
        
        # 状态栏
        self.setup_status_bar(main_frame)

    def setup_file_area(self, parent):
        """设置文件选择区域"""
        if DRAG_DROP_AVAILABLE:
            # 拖放区域 - 使用渐变色边框效果
            drop_outer = tk.Frame(parent, bg='#4a90e2', padx=2, pady=2)
            drop_outer.pack(fill=tk.X, pady=(0, 10))
            
            self.drop_zone = tk.Frame(
                drop_outer,
                bg=self.colors['drop_zone'],
                height=100
            )
            self.drop_zone.pack(fill=tk.BOTH, expand=True)
            self.drop_zone.pack_propagate(False)

            self.drop_label = tk.Label(
                self.drop_zone,
                text="🎯 将文件拖放到这里\n支持格式：PDF、JPG、PNG",
                font=("微软雅黑", 13),
                bg=self.colors['drop_zone'],
                fg='#4a90e2'
            )
            self.drop_label.pack(expand=True)
            
            # 设置拖放功能
            try:
                self.drop_zone.drop_target_register(DND_FILES)
                self.drop_zone.dnd_bind('<<DropEnter>>', self.on_drop_enter)
                self.drop_zone.dnd_bind('<<DropLeave>>', self.on_drop_leave)
                self.drop_zone.dnd_bind('<<Drop>>', self.on_drop)
            except:
                pass
        else:
            # 普通文件选择区域
            select_frame = tk.Frame(parent, bg=self.colors['bg'])
            select_frame.pack(fill=tk.X, pady=(0, 10))
            
            tk.Label(
                select_frame,
                text="📁 点击按钮选择文件（需要1个PDF + 2张图片）",
                font=("微软雅黑", 12),
                bg=self.colors['bg'],
                fg=self.colors['text']
            ).pack(pady=10)

    def setup_file_list(self, parent):
        """设置文件列表区域"""
        # 外层边框
        files_outer = tk.Frame(parent, bg='#d0d0d0', padx=1, pady=1)
        files_outer.pack(fill=tk.X, pady=(0, 10))
        
        files_frame = tk.Frame(files_outer, bg='white')
        files_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题栏
        title_bar = tk.Frame(files_frame, bg='#f8f9fa')
        title_bar.pack(fill=tk.X)
        tk.Label(title_bar, text="📁 已选择的文件", font=("微软雅黑", 10, "bold"), 
                bg='#f8f9fa', fg='#2c3e50', anchor='w').pack(padx=10, pady=6)

        self.file_listbox = tk.Listbox(
            files_frame,
            height=3,
            font=("微软雅黑", 10),
            bg='white',
            relief='flat',
            highlightthickness=0,
            selectbackground='#e8f4fd',
            selectforeground='#2c3e50'
        )
        self.file_listbox.pack(fill=tk.X, padx=8, pady=(0, 8))

    def setup_data_display(self, parent):
        """设置数据显示区域"""
        # 外层边框
        data_outer = tk.Frame(parent, bg='#52c41a', padx=1, pady=1)
        data_outer.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        data_frame = tk.Frame(data_outer, bg='white')
        data_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题栏 - 浅绿色
        title_bar = tk.Frame(data_frame, bg='#f6ffed')
        title_bar.pack(fill=tk.X)
        tk.Label(title_bar, text="🔍 提取的发票数据和智能命名预览", font=("微软雅黑", 10, "bold"), 
                bg='#f6ffed', fg='#389e0d', anchor='w').pack(padx=10, pady=6)

        self.data_text = tk.Text(
            data_frame,
            height=12,
            font=("Consolas", 9),
            bg='#fafffe',
            fg=self.colors['text'],
            state=tk.DISABLED,
            wrap=tk.WORD,
            relief='flat',
            highlightthickness=0,
            padx=8,
            pady=8
        )
        self.data_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        
        # 滚动条
        scrollbar = tk.Scrollbar(self.data_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.data_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.data_text.yview)

    def setup_buttons(self, parent):
        """设置按钮区域"""
        button_frame = tk.Frame(parent, bg=self.colors['bg'])
        button_frame.pack(fill=tk.X, pady=(0, 10))

        # 左侧按钮 - 选择文件（绿色渐变效果）
        self.select_btn = tk.Button(
            button_frame,
            text="📁 选择文件",
            font=("微软雅黑", 10, "bold"),
            bg='#52c41a',
            fg='white',
            activebackground='#73d13d',
            activeforeground='white',
            relief='flat',
            padx=18,
            pady=10,
            cursor='hand2',
            command=self.select_files
        )
        self.select_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 清除按钮（红色）
        self.clear_btn = tk.Button(
            button_frame,
            text="🗑️ 清除",
            font=("微软雅黑", 10, "bold"),
            bg='#ff4d4f',
            fg='white',
            activebackground='#ff7875',
            activeforeground='white',
            relief='flat',
            padx=18,
            pady=10,
            cursor='hand2',
            command=self.clear_files
        )
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 右侧：一键输出按钮（蓝色，更大更醒目）
        self.output_btn = tk.Button(
            button_frame,
            text="☑️ 一键输出",
            font=("微软雅黑", 12, "bold"),
            bg='#1890ff',
            fg='white',
            activebackground='#40a9ff',
            activeforeground='white',
            relief='flat',
            padx=30,
            pady=10,
            cursor='hand2',
            command=self.output_merged_file,
            state=tk.DISABLED
        )
        self.output_btn.pack(side=tk.RIGHT, padx=(10, 0))

    def setup_status_bar(self, parent):
        """设置状态栏"""
        status_frame = tk.Frame(parent, bg=self.colors['bg'])
        status_frame.pack(fill=tk.X)
        
        self.status_label = tk.Label(
            status_frame,
            text="请选择或拖放文件开始操作",
            font=("微软雅黑", 10),
            bg=self.colors['bg'],
            fg='#666666'
        )
        self.status_label.pack(side=tk.LEFT)

    # 拖放事件处理
    def on_drop_enter(self, event):
        if DRAG_DROP_AVAILABLE:
            self.drop_zone.config(bg=self.colors['drop_zone_active'])

    def on_drop_leave(self, event):
        if DRAG_DROP_AVAILABLE:
            self.drop_zone.config(bg=self.colors['drop_zone'])

    def on_drop(self, event):
        if DRAG_DROP_AVAILABLE:
            self.drop_zone.config(bg=self.colors['drop_zone'])
            files = self.root.tk.splitlist(event.data)
            self.add_files(files)

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

        self.update_display()

    def clear_files(self):
        """清除所有文件"""
        self.pdf_file = None
        self.image_files = []
        self.extracted_data = None
        self.update_display()

    def extract_data(self):
        """提取发票数据"""
        if not self.pdf_file or not PDF_AVAILABLE:
            return
            
        self.extract_btn.config(state=tk.DISABLED, text="🔄 提取中...")
        self.status_label.config(text="正在提取发票数据...")
        
        def extract_worker():
            try:
                data = self.extract_invoice_data(self.pdf_file)
                self.root.after(0, lambda: self.extract_success(data))
            except Exception as e:
                self.root.after(0, lambda: self.extract_failed(str(e)))
        
        thread = threading.Thread(target=extract_worker, daemon=True)
        thread.start()

    def extract_invoice_data(self, pdf_path: str) -> Dict[str, Any]:
        """从PDF中提取发票关键信息"""
        doc = pdfium.PdfDocument(pdf_path)
        full_text = ""
        
        for page_num in range(min(3, len(doc))):
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
        
        # 发票号码
        invoice_patterns = [r'发票号码[：:\s]*(\d{8,20})', r'(\d{20})', r'(\d{12})']
        data["invoice_number"] = self.extract_by_patterns(full_text, invoice_patterns) or "未识别"
            
        # 开票日期
        date_patterns = [r'开票日期[：:\s]*(\d{4}[-年]\d{1,2}[-月]\d{1,2}日?)', r'(\d{4}[-年]\d{1,2}[-月]\d{1,2}日?)']
        raw_date = self.extract_by_patterns(full_text, date_patterns)
        if raw_date:
            data["invoice_date"] = re.sub(r'年|月', '-', raw_date).replace('日', '')
        else:
            data["invoice_date"] = "未识别"
            
        # 金额 - 提取价税合计（含税总额）
        # 使用多种策略提取，确保获取包含税额的总金额
        data["amount"] = self.extract_total_amount(full_text)
            
        # 销售方名称
        seller_patterns = [r'销售方[：:\s]*([^\n\r]+?)(?:\s|纳税人)', r'卖方[：:\s]*([^\n\r]+?)(?:\s|纳税人)']
        seller_name = self.extract_by_patterns(full_text, seller_patterns)
        data["seller_name"] = seller_name[:10] if seller_name and len(seller_name) > 3 else "未识别"
        
        return data

    def extract_by_patterns(self, text: str, patterns: List[str]) -> Optional[str]:
        """使用多个正则模式提取文本"""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def extract_total_amount(self, text: str) -> float or str:
        """
        提取发票价税合计金额（含税总额）
        使用多种策略确保提取到正确的含税总金额
        """
        # 策略1: 查找"价税合计"关键字后的金额
        # 这是最可靠的方法，因为"价税合计"是法定的含税总额
        patterns_strategy1 = [
            # 匹配: 价税合计(大写)xxx(小写)¥123.45 或 价税合计(大写)xxx(小写) ¥123.45
            r'价税合计[\s\S]{0,50}?小写[）\)]*[：:\s]*¥?\s*([\d,，]+\.?\d*)',
            # 匹配: 价税合计...¥123.45 (在价税合计后100字符内查找¥符号)
            r'价税合计[\s\S]{0,100}?¥\s*([\d,，]+\.\d{2})',
            # 匹配: 价税合计 后面直接跟数字
            r'价税合计[：:\s]+¥?\s*([\d,，]+\.\d{2})',
        ]

        for pattern in patterns_strategy1:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                raw_amount = match.group(1)
                try:
                    clean_amount = raw_amount.replace(',', '').replace('，', '').strip()
                    amount = float(clean_amount)
                    # 金额合理性检查：一般发票金额在0.01-999999999之间
                    if 0.01 <= amount <= 999999999:
                        return amount
                except ValueError:
                    continue

        # 策略2: 查找"合计"相关字段（次优选择）
        patterns_strategy2 = [
            r'合计金额[：:\s]*¥?\s*([\d,，]+\.\d{2})',
            r'总金额[：:\s]*¥?\s*([\d,，]+\.\d{2})',
            r'应付金额[：:\s]*¥?\s*([\d,，]+\.\d{2})',
        ]

        for pattern in patterns_strategy2:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                raw_amount = match.group(1)
                try:
                    clean_amount = raw_amount.replace(',', '').replace('，', '').strip()
                    amount = float(clean_amount)
                    if 0.01 <= amount <= 999999999:
                        return amount
                except ValueError:
                    continue

        # 策略3: 查找发票中所有的金额，选择最大的一个（通常价税合计是最大值）
        # 这个策略作为最后的保底方案
        all_amounts = []
        amount_pattern = r'¥\s*([\d,，]+\.\d{2})'
        for match in re.finditer(amount_pattern, text):
            try:
                raw_amount = match.group(1)
                clean_amount = raw_amount.replace(',', '').replace('，', '').strip()
                amount = float(clean_amount)
                if 0.01 <= amount <= 999999999:
                    all_amounts.append(amount)
            except ValueError:
                continue

        if all_amounts:
            # 返回最大金额（通常就是价税合计）
            return max(all_amounts)

        return "未识别"

    def extract_success(self, data):
        """数据提取成功"""
        self.extracted_data = data
        self.extract_btn.config(state=tk.NORMAL, text="🔍 提取数据")
        self.status_label.config(text="✅ 数据提取成功！")
        self.update_display()

    def extract_failed(self, error_msg):
        """数据提取失败"""
        self.extract_btn.config(state=tk.NORMAL, text="🔍 提取数据")
        self.status_label.config(text="❌ 数据提取失败，将使用默认命名")
        self.update_display()

    def generate_filename(self, data: Dict[str, Any]) -> str:
        """生成新的文件名：姓名_组别_金额_发票后四位.pdf"""
        name = self.config_manager.get('name', '未命名')
        group = self.config_manager.get('group', '未分组')
        
        parts = [name, group]
        
        # 添加金额
        if data.get('amount') != "未识别":
            try:
                amount_str = f"{float(data['amount']):.2f}".replace('.00', '')
                parts.append(amount_str)
            except:
                parts.append("金额未知")
        else:
            parts.append("金额未知")
        
        # 添加发票号后4位
        if data.get('invoice_number') != "未识别":
            try:
                last4 = str(data['invoice_number'])[-4:]
                parts.append(last4)
            except:
                parts.append("0000")
        else:
            parts.append("0000")
        
        return '_'.join(parts) + '.pdf'

    def update_display(self):
        """更新显示"""
        # 更新文件列表
        self.file_listbox.delete(0, tk.END)
        if self.pdf_file:
            # 检测PDF页数
            try:
                if PDF_AVAILABLE:
                    doc = pdfium.PdfDocument(self.pdf_file)
                    page_count = len(doc)
                    doc.close()
                    self.file_listbox.insert(tk.END, f"📄 PDF: {os.path.basename(self.pdf_file)} ({page_count}页)")
                else:
                    self.file_listbox.insert(tk.END, f"📄 PDF: {os.path.basename(self.pdf_file)}")
            except:
                self.file_listbox.insert(tk.END, f"📄 PDF: {os.path.basename(self.pdf_file)}")
        
        for i, img_file in enumerate(self.image_files, 1):
            label = "购买记录" if i == 1 else "支付记录"
            self.file_listbox.insert(tk.END, f"🖼️ 图片{i}({label}): {os.path.basename(img_file)}")

        # 更新按钮状态
        if self.pdf_file and len(self.image_files) == 2:
            self.output_btn.config(state=tk.NORMAL)
            self.status_label.config(text="✅ 文件已就绪，可以输出")
        else:
            self.output_btn.config(state=tk.DISABLED)
            if not self.pdf_file:
                self.status_label.config(text="请选择PDF文件")
            elif len(self.image_files) != 2:
                self.status_label.config(text=f"需要2张图片，当前有{len(self.image_files)}张")

        # 更新数据显示
        self.data_text.config(state=tk.NORMAL)
        self.data_text.delete(1.0, tk.END)
        
        display_text = ""
        
        if self.pdf_file:
            original_name = os.path.basename(self.pdf_file)
            
            if self.extracted_data:
                display_text += "🔍 发票数据（从第一页提取）：\n"
                display_text += "=" * 50 + "\n"
                display_text += f"📄 文件名: {self.extracted_data.get('file_name', '未知')}\n"
                display_text += f"🔢 发票号码: {self.extracted_data.get('invoice_number', '未识别')}\n"
                display_text += f"📅 开票日期: {self.extracted_data.get('invoice_date', '未识别')}\n"
                display_text += f"💰 金额: ¥{self.extracted_data.get('amount', '未识别')}\n"
                display_text += f"🏢 销售方: {self.extracted_data.get('seller_name', '未识别')}\n"
                display_text += f"⏰ 提取时间: {self.extracted_data.get('extracted_at', '')}\n\n"
                
                new_filename = self.generate_filename(self.extracted_data)
                display_text += "📝 输出文件命名：\n"
                display_text += "-" * 30 + "\n"
                display_text += f"{new_filename}\n\n"
                # 显示输出位置
                output_dir, _ = self.get_output_directory()
                display_text += f"💡 输出位置：{output_dir or '未配置'}\n"
            else:
                display_text = "💡 使用说明：\n"
                display_text += "1. 选择或拖放1个PDF发票文件（支持多页）\n"
                display_text += "2. 选择或拖放2张图片（按顺序：购买记录、支付记录）\n"
                display_text += "3. 点击【一键输出】完成所有操作\n\n"
                display_text += "✨ 功能特色：\n"
                display_text += "• 支持多页PDF完整处理（发票每页占1/2区域）\n"
                display_text += "• 自动提取发票信息并智能命名\n"
                display_text += f"• 输出格式：{self.config_manager.get('name', '姓名')}_{self.config_manager.get('group', '组别')}_金额_发票后四位.pdf\n"
                output_dir, _ = self.get_output_directory()
                display_text += f"• 输出位置：{output_dir or '请配置输出路径'}"
        else:
            display_text = "💡 使用说明：\n"
            display_text += "1. 选择或拖放1个PDF发票文件（支持多页）\n"
            display_text += "2. 选择或拖放2张图片（按顺序：购买记录、支付记录）\n"
            display_text += "3. 点击【一键输出】完成所有操作"
        
        self.data_text.insert(1.0, display_text)
        self.data_text.config(state=tk.DISABLED)

    def merge_files(self):
        """合并文件"""
        if not (self.pdf_file and len(self.image_files) == 2):
            messagebox.showerror("文件不完整", "需要1个PDF文件和2张图片才能合并")
            return

        # 生成文件名
        original_filename = os.path.basename(self.pdf_file)
        if self.extracted_data:
            smart_filename = self.generate_smart_filename(self.extracted_data, original_filename)
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
            return

        self.merge_btn.config(state=tk.DISABLED, text="🔄 处理中...")
        self.status_label.config(text="正在合并文件...")

        try:
            # 创建临时文件
            temp_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            temp_buy = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)  
            temp_pay = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
            
            temp_pdf.close()
            temp_buy.close()
            temp_pay.close()

            # 复制文件
            shutil.copy2(self.pdf_file, temp_pdf.name)
            sorted_images = sorted(self.image_files, key=lambda x: os.path.basename(x).lower())
            shutil.copy2(sorted_images[0], temp_buy.name)
            shutil.copy2(sorted_images[1], temp_pay.name)

            # 调用合并函数
            merge_simple(temp_pdf.name, temp_buy.name, temp_pay.name, output_path)

            # 清理临时文件
            for temp_file in [temp_pdf.name, temp_buy.name, temp_pay.name]:
                try:
                    os.unlink(temp_file)
                except:
                    pass

            self.merge_btn.config(state=tk.NORMAL, text="🚀 智能合并")
            self.status_label.config(text="✅ 合并成功！文件已保存")

            # 自动清除文件，准备处理下一张
            self.clear_files()

        except Exception as e:
            self.merge_btn.config(state=tk.NORMAL, text="🚀 智能合并")
            self.status_label.config(text="❌ 合并失败")
            messagebox.showerror("合并失败", f"合并过程中出现错误：\n{e}")

    def output_merged_file(self):
        """一键输出：提取数据+合并PDF+自动命名+保存到配置的输出目录"""
        # 检查文件是否已选择
        if not self.pdf_file or len(self.image_files) != 2:
            messagebox.showwarning("提示", "请先选择所有必需的文件：\n- 发票PDF\n- 购买记录截图\n- 支付记录截图")
            return
        
        # 检查输出目录是否有效
        output_dir, error_msg = self.get_output_directory()
        if error_msg:
            messagebox.showerror("输出路径错误", error_msg)
            return
        
        # 禁用按钮，防止重复点击
        self.output_btn.config(state=tk.DISABLED, text="🔄 处理中...")
        self.status_label.config(text="正在处理...")
        
        # 用于存储警告信息
        warnings = []
        
        # 在后台线程中处理
        def output_worker():
            nonlocal warnings
            try:
                # 1. 验证PDF文件是否有效
                self.root.after(0, lambda: self.status_label.config(text="正在验证PDF文件..."))
                try:
                    import pypdfium2 as pdfium
                    doc = pdfium.PdfDocument(self.pdf_file)
                    page_count = len(doc)
                    doc.close()
                    if page_count == 0:
                        raise ValueError("PDF文件没有任何页面")
                except Exception as pdf_err:
                    raise ValueError(f"无法读取PDF文件，请确认选择的是有效的发票PDF文件。\n\n错误详情: {pdf_err}")
                
                # 2. 提取发票数据
                self.root.after(0, lambda: self.status_label.config(text="正在提取发票数据..."))
                invoice_data = self.extract_invoice_data(self.pdf_file)
                
                # 3. 验证提取的数据是否有效（判断是否为发票）
                invoice_number = invoice_data.get('invoice_number', '未识别')
                amount = invoice_data.get('amount', '未识别')
                
                # 收集警告信息
                if amount == '未识别':
                    warnings.append("⚠️ 未能识别发票金额，文件名中金额显示为0")
                if invoice_number == '未识别':
                    warnings.append("⚠️ 未能识别发票号码，文件名中发票后四位显示为0000")
                
                if invoice_number == '未识别' and amount == '未识别':
                    self.root.after(0, lambda: self.status_label.config(text="⚠️ 未能识别发票信息，继续合并..."))
                
                # 4. 生成文件名
                output_filename = self.generate_filename(invoice_data)
                
                # 5. 确定输出路径
                output_path = os.path.join(output_dir, output_filename)
                
                # 6. 检查文件是否已存在（重复导出检测）
                if os.path.exists(output_path):
                    # 在主线程中询问用户
                    result = {'overwrite': False, 'cancelled': False}
                    def ask_overwrite():
                        response = messagebox.askyesnocancel(
                            "文件已存在", 
                            f"输出目录中已存在同名文件：\n{output_filename}\n\n可能是重复导出的发票。\n\n是否覆盖？\n• 是 - 覆盖现有文件\n• 否 - 自动添加序号\n• 取消 - 取消操作"
                        )
                        if response is None:
                            result['cancelled'] = True
                        elif response:
                            result['overwrite'] = True
                        else:
                            # 添加序号
                            base, ext = os.path.splitext(output_filename)
                            counter = 1
                            while os.path.exists(os.path.join(output_dir, f"{base}_{counter}{ext}")):
                                counter += 1
                            result['new_filename'] = f"{base}_{counter}{ext}"
                    
                    self.root.after(0, ask_overwrite)
                    # 等待用户响应
                    import time
                    while 'new_filename' not in result and not result['overwrite'] and not result['cancelled']:
                        time.sleep(0.1)
                        if result['overwrite'] or result['cancelled']:
                            break
                    
                    if result['cancelled']:
                        self.root.after(0, lambda: self.output_cancelled())
                        return
                    
                    if 'new_filename' in result:
                        output_path = os.path.join(output_dir, result['new_filename'])
                
                # 7. 合并PDF（使用多页支持）
                self.root.after(0, lambda: self.status_label.config(text="正在合并PDF..."))
                
                from merge_invoices_v6 import merge_with_multi_pages
                
                # 调用多页合并（使用位置参数）
                merge_with_multi_pages(
                    self.pdf_file,
                    self.image_files[0],
                    self.image_files[1],
                    output_path
                )
                
                # 完成，显示成功消息
                self.root.after(0, lambda p=output_path, w=warnings: self.output_success(p, w))
                
            except ValueError as ve:
                # 验证错误，给出友好提示
                error_msg = str(ve)
                self.root.after(0, lambda msg=error_msg: self.output_failed(msg))
            except Exception as e:
                # 其他错误
                error_msg = f"处理过程中出现错误：\n{str(e)}\n\n请检查：\n1. PDF文件是否为有效的发票文件\n2. 图片文件是否完整\n3. 文件是否被其他程序占用"
                self.root.after(0, lambda msg=error_msg: self.output_failed(msg))
        
        # 启动后台线程
        thread = threading.Thread(target=output_worker, daemon=True)
        thread.start()
    
    def output_cancelled(self):
        """输出取消回调"""
        self.output_btn.config(state=tk.NORMAL, text="✅ 一键输出")
        self.status_label.config(text="已取消操作")
    
    def output_success(self, output_path: str, warnings: list = None):
        """输出成功回调"""
        self.output_btn.config(state=tk.NORMAL, text="✅ 一键输出")
        self.status_label.config(text="✅ 输出成功！")
        
        # 构建成功消息
        success_msg = f"已成功生成文件：\n{os.path.basename(output_path)}\n\n保存位置：\n{os.path.dirname(output_path)}"
        
        # 添加警告信息
        if warnings:
            success_msg += "\n\n" + "=" * 30 + "\n"
            success_msg += "提示信息：\n"
            success_msg += "\n".join(warnings)
        
        messagebox.showinfo("输出成功", success_msg)
        
        # 自动清除文件，准备处理下一张
        self.clear_files()
    
    def output_failed(self, error_msg: str):
        """输出失败回调"""
        self.output_btn.config(state=tk.NORMAL, text="✅ 一键输出")
        self.status_label.config(text="❌ 输出失败")
        messagebox.showerror("输出失败", f"输出过程中出现错误：\n{error_msg}")

    def run(self):
        """运行主程序"""
        # 居中显示窗口
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        # 首次运行检查 - 在主窗口显示后弹出配置对话框
        if self.config_manager.is_first_run():
            self.root.after(200, self._show_first_run_config)

        # 初始化显示
        self.root.after(100, self.update_display)
        self.root.mainloop()
    
    def _show_first_run_config(self):
        """首次运行时显示配置对话框"""
        messagebox.showinfo(
            "欢迎使用", 
            "首次使用，请先设置您的基本信息。",
            parent=self.root
        )
        if not self.show_config_dialog(is_first_run=True):
            # 如果用户取消，设置默认值
            self.config_manager.set('name', '未设置')
            self.config_manager.set('group', '未设置')
        self.update_config_display()


def main():
    """主入口"""
    try:
        app = SimpleInvoiceMergerV6()
        app.run()
        return 0
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("启动失败", f"程序启动失败：\n{e}")
            root.destroy()
        except:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())