#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
发票合并工具 - 可执行版本
带图形化用户提示的友好版本
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import os
import sys
import threading
from pathlib import Path

# 导入原有的合并逻辑
try:
    from merge_invoices import main as merge_main
except ImportError:
    # 如果打包后找不到模块，尝试从当前目录导入
    import importlib.util
    current_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
    merge_script = os.path.join(current_dir, 'merge_invoices.py')
    if os.path.exists(merge_script):
        spec = importlib.util.spec_from_file_location("merge_invoices", merge_script)
        merge_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(merge_module)
        merge_main = merge_module.main
    else:
        # 最后的备用方案：内嵌合并逻辑
        def merge_main(args):
            print("错误：无法找到合并逻辑模块")
            return 1


class InvoiceMergerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("发票合并工具 v2.0")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # 设置图标（如果有的话）
        try:
            # self.root.iconbitmap("icon.ico")  # 可以添加图标
            pass
        except:
            pass
            
        self.setup_ui()
        
    def setup_ui(self):
        # 标题
        title_label = tk.Label(
            self.root, 
            text="📄 发票合并工具", 
            font=("微软雅黑", 16, "bold"),
            fg="#2c3e50"
        )
        title_label.pack(pady=(15, 10))
        
        # 说明文字
        info_text = """
本工具可以自动合并发票PDF与对应的购买记录、支付记录图片。

文件命名规则：
• PDF发票：任意名称.pdf
• 购买记录：相同名称 + 购买记录.jpg/png
• 支付记录：相同名称 + 支付记录.jpg/png

示例：
• 1开发板19.9.pdf
• 1开发板19.9购买记录.jpg  
• 1开发板19.9支付记录.jpg
        """
        
        info_label = tk.Label(
            self.root, 
            text=info_text, 
            font=("微软雅黑", 9),
            justify="left",
            fg="#34495e",
            wraplength=550
        )
        info_label.pack(pady=(5, 15), padx=20)
        
        # 按钮区域
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=(10, 15))
        
        # 选择目录按钮
        select_btn = tk.Button(
            button_frame,
            text="📁 选择发票目录",
            font=("微软雅黑", 12),
            bg="#3498db",
            fg="white",
            padx=20,
            pady=10,
            command=self.select_directory
        )
        select_btn.pack(side="left", padx=10)
        
        # 使用当前目录按钮
        current_btn = tk.Button(
            button_frame,
            text="📍 使用当前目录",
            font=("微软雅黑", 12),
            bg="#27ae60",
            fg="white",
            padx=20,
            pady=10,
            command=self.use_current_directory
        )
        current_btn.pack(side="left", padx=10)
        
        # 进度显示
        self.status_label = tk.Label(
            self.root,
            text="请选择包含发票文件的目录",
            font=("微软雅黑", 10),
            fg="#7f8c8d"
        )
        self.status_label.pack(pady=(5, 10))
        
        # 结果显示区域
        self.result_text = tk.Text(
            self.root,
            height=10,
            font=("Consolas", 9),
            bg="#f8f9fa",
            fg="#2c3e50"
        )
        self.result_text.pack(pady=(5, 15), padx=20, fill="both", expand=True)
        
        # 滚动条
        scrollbar = tk.Scrollbar(self.result_text)
        scrollbar.pack(side="right", fill="y")
        self.result_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.result_text.yview)
        
    def select_directory(self):
        directory = filedialog.askdirectory(title="选择包含发票文件的目录")
        if directory:
            self.process_directory(directory)
            
    def use_current_directory(self):
        # 获取可执行文件所在目录作为当前目录
        if getattr(sys, 'frozen', False):
            # 打包后的可执行文件
            current_dir = os.path.dirname(sys.executable)
        else:
            # 开发环境
            current_dir = os.getcwd()
            
        result = messagebox.askyesno(
            "确认", 
            f"确定要处理当前目录的发票文件吗？\n\n当前目录：\n{current_dir}"
        )
        if result:
            self.process_directory(current_dir)
            
    def process_directory(self, directory):
        self.status_label.config(text=f"正在处理: {directory}")
        self.result_text.delete(1.0, tk.END)
        
        # 在新线程中执行合并操作，避免界面卡顿
        thread = threading.Thread(
            target=self.run_merge,
            args=(directory,)
        )
        thread.daemon = True
        thread.start()
        
    def run_merge(self, directory):
        try:
            # 记录原始工作目录
            original_cwd = os.getcwd()
            
            # 重定向输出到GUI
            import io
            from contextlib import redirect_stdout, redirect_stderr
            
            output_buffer = io.StringIO()
            
            # 直接传递目录参数，不切换工作目录
            with redirect_stdout(output_buffer), redirect_stderr(output_buffer):
                result_code = merge_main([directory])
            
            # 获取输出内容
            output = output_buffer.getvalue()
            
            # 确保工作目录没有被意外改变
            if os.getcwd() != original_cwd:
                os.chdir(original_cwd)
            
            # 更新GUI（需要在主线程中执行）
            self.root.after(0, self.update_result, directory, output, result_code)
            
        except Exception as e:
            # 恢复工作目录
            try:
                os.chdir(original_cwd)
            except:
                pass
            self.root.after(0, self.show_error, str(e))
            
    def update_result(self, directory, output, result_code):
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, output)
        
        if result_code == 0:
            self.status_label.config(text="✅ 处理完成！合并文件已保存到'已合并'目录")
            messagebox.showinfo(
                "处理完成", 
                f"发票合并完成！\n\n处理目录：{directory}\n输出目录：{directory}/已合并"
            )
        else:
            self.status_label.config(text="❌ 处理过程中出现问题")
            messagebox.showwarning("注意", "处理完成，但可能存在一些问题，请查看详细信息。")
            
    def show_error(self, error_msg):
        self.status_label.config(text="❌ 处理失败")
        messagebox.showerror("错误", f"处理过程中发生错误：\n{error_msg}")
        
    def run(self):
        # 居中显示窗口
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        self.root.mainloop()


def main():
    """主入口函数"""
    try:
        # 如果是在没有显示的环境下运行，使用命令行模式
        if len(sys.argv) > 1 and sys.argv[1] == "--cli":
            return merge_main(sys.argv[2:])
        
        # 尝试启动GUI
        app = InvoiceMergerGUI()
        app.run()
        return 0
        
    except Exception as e:
        # GUI启动失败时回退到命令行模式
        print(f"GUI启动失败，使用命令行模式: {e}")
        return merge_main(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())