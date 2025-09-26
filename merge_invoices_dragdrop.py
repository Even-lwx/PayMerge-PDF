#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
发票合并工具 - 拖放版本 v4.0
支持直接拖放一个PDF和两张图片进行合并
"""

import tkinter as tk
from tkinter import messagebox, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
import sys
import threading
from pathlib import Path
import shutil
import tempfile
from typing import List, Optional, Tuple

# 导入原有的合并逻辑
try:
    from merge_invoices_simple import merge_simple
except ImportError:
    # 如果找不到简化版本，我们稍后会创建它
    pass


class DragDropInvoiceMerger:
    def __init__(self):
        self.root = TkinterDnD.Tk()
        self.root.title("发票合并工具 v4.0 - 拖放版")
        self.root.geometry("700x600")
        self.root.resizable(True, True)

        # 文件存储
        self.pdf_file = None
        self.image_files = []

        # 颜色主题
        self.colors = {
            'bg': '#f0f0f0',
            'drop_zone': '#e8f4fd',
            'drop_zone_active': '#c3e7fd',
            'button': '#4a90e2',
            'button_hover': '#357abd',
            'success': '#52c41a',
            'error': '#f5222d',
            'text': '#333333'
        }

        self.setup_ui()

    def setup_ui(self):
        self.root.configure(bg=self.colors['bg'])

        # 标题
        title_label = tk.Label(
            self.root,
            text="📄 发票合并工具 - 拖放版",
            font=("微软雅黑", 18, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        title_label.pack(pady=(20, 10))

        # 说明文字
        info_label = tk.Label(
            self.root,
            text="拖放文件到下方区域：1个PDF发票 + 2张图片（购买记录和支付记录）",
            font=("微软雅黑", 11),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        info_label.pack(pady=(0, 20))

        # 主容器
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 20))

        # 拖放区域
        self.drop_zone = tk.Frame(
            main_frame,
            bg=self.colors['drop_zone'],
            relief=tk.RIDGE,
            borderwidth=3,
            height=250
        )
        self.drop_zone.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # 拖放区域内的提示
        self.drop_label = tk.Label(
            self.drop_zone,
            text="🎯\n\n将文件拖放到这里\n\n支持格式：PDF, JPG, PNG",
            font=("微软雅黑", 14),
            bg=self.colors['drop_zone'],
            fg='#666666'
        )
        self.drop_label.pack(expand=True)

        # 文件列表显示区域
        files_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        files_frame.pack(fill=tk.BOTH, pady=(0, 15))

        tk.Label(
            files_frame,
            text="已选择的文件：",
            font=("微软雅黑", 11, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['text']
        ).pack(anchor='w')

        # 文件列表
        list_frame = tk.Frame(files_frame, bg='white', relief=tk.SUNKEN, borderwidth=1)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        self.file_listbox = tk.Listbox(
            list_frame,
            height=5,
            font=("微软雅黑", 10),
            selectmode=tk.SINGLE,
            bg='white'
        )
        self.file_listbox.pack(fill=tk.BOTH, expand=True)

        # 滚动条
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.file_listbox.yview)

        # 按钮区域
        button_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        button_frame.pack(fill=tk.X)

        # 清除按钮
        self.clear_btn = tk.Button(
            button_frame,
            text="🗑️ 清除所有",
            font=("微软雅黑", 11),
            bg='#ff7875',
            fg='white',
            padx=15,
            pady=8,
            relief=tk.FLAT,
            command=self.clear_files
        )
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 选择文件按钮
        self.select_btn = tk.Button(
            button_frame,
            text="📁 选择文件",
            font=("微软雅黑", 11),
            bg='#95de64',
            fg='white',
            padx=15,
            pady=8,
            relief=tk.FLAT,
            command=self.select_files
        )
        self.select_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 合并按钮
        self.merge_btn = tk.Button(
            button_frame,
            text="✨ 开始合并",
            font=("微软雅黑", 12, "bold"),
            bg=self.colors['button'],
            fg='white',
            padx=20,
            pady=8,
            relief=tk.FLAT,
            state=tk.DISABLED,
            command=self.merge_files
        )
        self.merge_btn.pack(side=tk.RIGHT)

        # 状态栏
        self.status_label = tk.Label(
            self.root,
            text="请拖放或选择文件",
            font=("微软雅黑", 10),
            bg=self.colors['bg'],
            fg='#666666'
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 10))

        # 设置拖放功能
        self.setup_drag_drop()

    def setup_drag_drop(self):
        """设置拖放功能"""
        self.drop_zone.drop_target_register(DND_FILES)
        self.drop_zone.dnd_bind('<<Drop>>', self.on_drop)
        self.drop_zone.dnd_bind('<<DragEnter>>', self.on_drag_enter)
        self.drop_zone.dnd_bind('<<DragLeave>>', self.on_drag_leave)

    def on_drag_enter(self, event):
        """鼠标拖动文件进入时"""
        self.drop_zone.configure(bg=self.colors['drop_zone_active'])
        self.drop_label.configure(bg=self.colors['drop_zone_active'])

    def on_drag_leave(self, event):
        """鼠标拖动文件离开时"""
        self.drop_zone.configure(bg=self.colors['drop_zone'])
        self.drop_label.configure(bg=self.colors['drop_zone'])

    def on_drop(self, event):
        """文件拖放时"""
        self.drop_zone.configure(bg=self.colors['drop_zone'])
        self.drop_label.configure(bg=self.colors['drop_zone'])

        # 解析文件路径
        files = self.parse_drop_data(event.data)
        self.add_files(files)

    def parse_drop_data(self, data: str) -> List[str]:
        """解析拖放数据，处理带空格的路径"""
        files = []

        # Windows系统的处理
        if sys.platform == 'win32':
            # 处理带花括号的路径（Windows特有）
            if data.startswith('{') and '}' in data:
                parts = data.split('}')
                for part in parts:
                    if part.startswith('{'):
                        part = part[1:]
                    part = part.strip()
                    if part:
                        files.append(part)
            else:
                # 简单的空格分隔
                files = data.split()
        else:
            # Unix系统的处理
            files = data.split()

        return [f for f in files if os.path.isfile(f)]

    def add_files(self, files: List[str]):
        """添加文件到列表"""
        for file_path in files:
            if not os.path.isfile(file_path):
                continue

            _, ext = os.path.splitext(file_path)
            ext = ext.lower()

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
        self.update_file_list()

    def update_file_list(self):
        """更新文件列表显示"""
        self.file_listbox.delete(0, tk.END)

        if self.pdf_file:
            self.file_listbox.insert(tk.END, f"📄 PDF: {os.path.basename(self.pdf_file)}")

        for i, img_file in enumerate(self.image_files, 1):
            self.file_listbox.insert(tk.END, f"🖼️ 图片{i}: {os.path.basename(img_file)}")

        # 检查是否可以合并
        if self.pdf_file and len(self.image_files) == 2:
            self.merge_btn.config(state=tk.NORMAL)
            self.status_label.config(text="✅ 文件已就绪，可以开始合并")
        else:
            self.merge_btn.config(state=tk.DISABLED)
            missing = []
            if not self.pdf_file:
                missing.append("PDF文件")
            if len(self.image_files) < 2:
                missing.append(f"{2 - len(self.image_files)}张图片")
            self.status_label.config(text=f"还需要：{', '.join(missing)}")

    def merge_files(self):
        """执行合并操作"""
        if not self.pdf_file or len(self.image_files) != 2:
            messagebox.showerror("错误", "请确保已选择1个PDF文件和2张图片")
            return

        # 禁用按钮
        self.merge_btn.config(state=tk.DISABLED)
        self.status_label.config(text="正在合并文件...")

        # 在新线程中执行合并
        thread = threading.Thread(target=self.do_merge)
        thread.daemon = True
        thread.start()

    def do_merge(self):
        """执行实际的合并操作"""
        try:
            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                # 复制文件到临时目录，使用固定名称
                temp_pdf = os.path.join(temp_dir, "invoice.pdf")
                temp_buy = os.path.join(temp_dir, "buy.jpg")
                temp_pay = os.path.join(temp_dir, "pay.jpg")

                shutil.copy2(self.pdf_file, temp_pdf)

                # 复制图片（保持原格式）
                for i, img_file in enumerate(self.image_files):
                    _, ext = os.path.splitext(img_file)
                    if i == 0:
                        target = os.path.join(temp_dir, f"buy{ext}")
                    else:
                        target = os.path.join(temp_dir, f"pay{ext}")
                    shutil.copy2(img_file, target)

                    if i == 0:
                        temp_buy = target
                    else:
                        temp_pay = target

                # 生成输出文件名
                pdf_base = os.path.splitext(os.path.basename(self.pdf_file))[0]
                output_name = f"{pdf_base}_已合并.pdf"

                # 弹出保存对话框
                output_path = filedialog.asksaveasfilename(
                    title="保存合并后的PDF",
                    defaultextension=".pdf",
                    initialfile=output_name,
                    filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
                )

                if not output_path:
                    self.root.after(0, self.merge_cancelled)
                    return

                # 调用合并函数
                from merge_invoices_simple import merge_simple
                merge_simple(temp_pdf, temp_buy, temp_pay, output_path)

                # 成功
                self.root.after(0, self.merge_success, output_path)

        except Exception as e:
            self.root.after(0, self.merge_failed, str(e))

    def merge_cancelled(self):
        """合并取消"""
        self.merge_btn.config(state=tk.NORMAL)
        self.status_label.config(text="合并已取消")

    def merge_success(self, output_path):
        """合并成功"""
        self.merge_btn.config(state=tk.NORMAL)
        self.status_label.config(text="✅ 合并成功！")

        result = messagebox.askyesno(
            "合并成功",
            f"文件已保存到：\n{output_path}\n\n是否打开文件所在目录？"
        )

        if result:
            # 打开文件所在目录
            output_dir = os.path.dirname(output_path)
            if sys.platform == 'win32':
                os.startfile(output_dir)
            elif sys.platform == 'darwin':
                os.system(f'open "{output_dir}"')
            else:
                os.system(f'xdg-open "{output_dir}"')

        # 询问是否继续
        if messagebox.askyesno("继续", "是否继续合并其他文件？"):
            self.clear_files()

    def merge_failed(self, error_msg):
        """合并失败"""
        self.merge_btn.config(state=tk.NORMAL)
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

        self.root.mainloop()


def main():
    """主入口"""
    try:
        app = DragDropInvoiceMerger()
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