#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Invoice Merge Script - Adaptive Layout Version

This script automatically merges invoice PDFs with corresponding purchase and payment record images.
It uses intelligent layout algorithms to optimize space utilization based on image dimensions.

Key Features:
- Adaptive layout selection (horizontal or vertical)
- Proportional scaling without distortion
- Automatic space optimization
- Preserves original files
"""

from __future__ import annotations

import os
import sys
from io import BytesIO
from typing import Dict, Optional, Tuple, Any

from PIL import Image
import pypdfium2 as pdfium


ALLOWED_IMG_EXTS = {".jpg", ".jpeg", ".png"}


def debug(msg: str) -> None:
    print(msg)


def split_suffix(filename: str) -> Tuple[str, str]:
    """返回 (无扩展名, 扩展名小写)"""
    base, ext = os.path.splitext(filename)
    return base, ext.lower()


def is_source_pdf(filename: str) -> bool:
    base, ext = split_suffix(filename)
    if ext != ".pdf":
        return False
    # 排除已合并产物
    return not base.endswith("已合并")


def classify_file(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """根据命名识别类型
    返回 (base_key, kind)
    kind ∈ {"pdf", "buy", "pay"} 或 None
    base_key 为不含后缀的"编号+名称+价格"原始基名
    """
    base, ext = split_suffix(filename)
    if ext == ".pdf" and not base.endswith("已合并"):
        # 形如 X.pdf
        return base, "pdf"

    if ext in ALLOWED_IMG_EXTS:
        if base.endswith("购买记录"):
            return base[: -len("购买记录")], "buy"
        if base.endswith("支付记录"):
            return base[: -len("支付记录")], "pay"

    return None, None


def build_index(root: str) -> Dict[str, Dict[str, str]]:
    """扫描目录并建立 base_key -> {pdf,buy,pay} 的路径索引"""
    index: Dict[str, Dict[str, str]] = {}
    for name in os.listdir(root):
        path = os.path.join(root, name)
        if not os.path.isfile(path):
            continue
        base, kind = classify_file(name)
        if not base or not kind:
            continue
        bucket = index.setdefault(base, {})
        bucket[kind] = path
    return index


def ensure_output_dir(root: str) -> str:
    out_dir = os.path.join(root, "已合并")
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def render_invoice_first_page_as_image(pdf_path: str, dpi: int = 300) -> Image.Image:
    """用 pypdfium2 将源 PDF 的第一页渲染为 PIL Image（RGB）。"""
    scale = dpi / 72.0
    pdf = pdfium.PdfDocument(pdf_path)
    try:
        if len(pdf) == 0:
            raise ValueError(f"源 PDF 无页面: {pdf_path}")
        page = pdf[0]
        try:
            bitmap = page.render(scale=scale)
            img = bitmap.to_pil()
        finally:
            page.close()
    finally:
        pdf.close()
    return img.convert("RGB")


def make_single_page_pdf(invoice_img: Image.Image, buy_img_path: str, pay_img_path: str) -> bytes:
    """使用 Pillow 生成最终单页 PDF（A4 纵向、白底），智能自适应布局。
    根据三张图片的实际尺寸和比例，动态调整布局以最大化利用空间。
    """
    a4_w_mm, a4_h_mm = 210.0, 297.0
    margin_mm = 15.0  # 边距
    dpi = 300

    def mm_to_px(mm: float) -> int:
        return int(round(mm / 25.4 * dpi))

    page_w = mm_to_px(a4_w_mm)
    page_h = mm_to_px(a4_h_mm)
    margin = mm_to_px(margin_mm)

    # 内容区域尺寸
    content_w = page_w - margin * 2
    content_h = page_h - margin * 2

    # 画布
    canvas_img = Image.new("RGB", (page_w, page_h), color=(255, 255, 255))

    def open_as_rgb(path: str) -> Image.Image:
        img = Image.open(path)
        return img.convert("RGB")

    def fit_into(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
        """等比缩放图片以适应指定区域"""
        iw, ih = img.size
        scale = min(max_w / iw, max_h / ih)
        new_w = max(1, int(round(iw * scale)))
        new_h = max(1, int(round(ih * scale)))
        try:
            Resampling = getattr(Image, "Resampling")
            resample = getattr(Resampling, "LANCZOS")
        except Exception:
            bicubic = getattr(Image, "BICUBIC", 3)
            resample = getattr(Image, "LANCZOS", getattr(Image, "ANTIALIAS", bicubic))
        return img.resize((new_w, new_h), resample)

    def get_best_orientation(img: Image.Image, max_w: int, max_h: int) -> Tuple[Image.Image, float]:
        """测试图片原始方向和旋转90度后的效果，返回更适合的方向和缩放系数"""
        w, h = img.size
        
        # 原始方向的缩放系数
        scale_original = min(max_w / w, max_h / h)
        
        # 旋转90度后的缩放系数
        scale_rotated = min(max_w / h, max_h / w)
        
        # 选择缩放系数更大的方向（即图片更大的方向）
        if scale_rotated > scale_original:
            rotated_img = img.rotate(90, expand=True)
            return rotated_img, scale_rotated
        else:
            return img, scale_original

    def get_optimal_layout(invoice_size: Tuple[int, int], buy_size: Tuple[int, int], pay_size: Tuple[int, int]) -> Dict[str, Any]:
        """根据三张图片的尺寸计算最优布局，考虑旋转可能性"""
        # 测试所有图片的最佳方向组合
        best_layout = None
        best_score = 0
        best_orientations = {}
        
        # 遍历所有可能的旋转组合（2^3 = 8种组合）
        for inv_rot in [False, True]:  # 发票是否旋转
            for buy_rot in [False, True]:  # 购买记录是否旋转
                for pay_rot in [False, True]:  # 支付记录是否旋转
                    
                    # 计算旋转后的尺寸
                    inv_w, inv_h = invoice_size if not inv_rot else (invoice_size[1], invoice_size[0])
                    buy_w, buy_h = buy_size if not buy_rot else (buy_size[1], buy_size[0])
                    pay_w, pay_h = pay_size if not pay_rot else (pay_size[1], pay_size[0])
                    
                    # 计算各图片的宽高比
                    inv_ratio = inv_w / inv_h
                    buy_ratio = buy_w / buy_h
                    pay_ratio = pay_w / pay_h
                    
                    # 测试方案1: 发票占上部，两图片并排占下部
                    max_inv_h_1 = min(content_h * 0.7, content_w / inv_ratio)
                    inv_scale_1 = min(content_w / inv_w, max_inv_h_1 / inv_h)
                    actual_inv_h_1 = int(inv_h * inv_scale_1)
                    
                    remaining_h_1 = content_h - actual_inv_h_1 - mm_to_px(5)
                    if remaining_h_1 > 0:
                        total_width_ratio = buy_ratio + pay_ratio
                        buy_area_w_1 = int(content_w * (buy_ratio / total_width_ratio))
                        pay_area_w_1 = content_w - buy_area_w_1
                        
                        buy_scale_1 = min(buy_area_w_1 / buy_w, remaining_h_1 / buy_h)
                        pay_scale_1 = min(pay_area_w_1 / pay_w, remaining_h_1 / pay_h)
                    else:
                        buy_scale_1 = pay_scale_1 = 0
                    
                    layout_1_score = inv_scale_1 + buy_scale_1 + pay_scale_1
                    
                    # 测试方案2: 发票占左侧，两图片纵向排列占右侧
                    max_inv_w_2 = min(content_w * 0.65, content_h * inv_ratio)
                    inv_scale_2 = min(max_inv_w_2 / inv_w, content_h / inv_h)
                    actual_inv_w_2 = int(inv_w * inv_scale_2)
                    
                    remaining_w_2 = content_w - actual_inv_w_2 - mm_to_px(5)
                    if remaining_w_2 > 0:
                        each_h_2 = content_h // 2
                        buy_scale_2 = min(remaining_w_2 / buy_w, each_h_2 / buy_h)
                        pay_scale_2 = min(remaining_w_2 / pay_w, each_h_2 / pay_h)
                    else:
                        buy_scale_2 = pay_scale_2 = 0
                        
                    layout_2_score = inv_scale_2 + buy_scale_2 + pay_scale_2
                    
                    # 选择当前组合下的最佳布局
                    if layout_1_score >= layout_2_score:
                        current_score = layout_1_score
                        current_layout = {
                            'type': 'horizontal',
                            'invoice_area': (0, 0, content_w, actual_inv_h_1),
                            'buy_area': (0, actual_inv_h_1 + mm_to_px(5), buy_area_w_1, remaining_h_1),
                            'pay_area': (buy_area_w_1, actual_inv_h_1 + mm_to_px(5), pay_area_w_1, remaining_h_1)
                        }
                    else:
                        current_score = layout_2_score
                        current_layout = {
                            'type': 'vertical',
                            'invoice_area': (0, 0, actual_inv_w_2, content_h),
                            'buy_area': (actual_inv_w_2 + mm_to_px(5), 0, remaining_w_2, each_h_2),
                            'pay_area': (actual_inv_w_2 + mm_to_px(5), each_h_2, remaining_w_2, each_h_2)
                        }
                    
                    # 更新全局最佳方案
                    if current_score > best_score:
                        best_score = current_score
                        best_layout = current_layout
                        best_orientations = {
                            'invoice_rotate': inv_rot,
                            'buy_rotate': buy_rot,
                            'pay_rotate': pay_rot
                        }
        
        # 添加旋转信息到布局结果中
        best_layout['orientations'] = best_orientations
        return best_layout

    # 准备三张图片
    invoice_rgb = invoice_img.convert("RGB")
    buy_rgb = open_as_rgb(buy_img_path)
    pay_rgb = open_as_rgb(pay_img_path)
    
    # 计算最优布局（包含旋转信息）
    layout = get_optimal_layout(invoice_rgb.size, buy_rgb.size, pay_rgb.size)
    orientations = layout['orientations']
    
    # 根据最优方案旋转图片
    if orientations['invoice_rotate']:
        invoice_rgb = invoice_rgb.rotate(90, expand=True)
        debug("发票图片旋转90度以优化布局")
    
    if orientations['buy_rotate']:
        buy_rgb = buy_rgb.rotate(90, expand=True)
        debug("购买记录图片旋转90度以优化布局")
    
    if orientations['pay_rotate']:
        pay_rgb = pay_rgb.rotate(90, expand=True)
        debug("支付记录图片旋转90度以优化布局")
    
    def paste_in_area(img: Image.Image, area: Tuple[int, int, int, int]) -> None:
        """在指定区域内居中粘贴图片"""
        area_x, area_y, area_w, area_h = area
        fitted_img = fit_into(img, area_w, area_h)
        
        # 计算居中位置
        img_w, img_h = fitted_img.size
        x = margin + area_x + (area_w - img_w) // 2
        y = margin + area_y + (area_h - img_h) // 2
        
        canvas_img.paste(fitted_img, (x, y))
    
    # 按布局粘贴三张图片（已应用旋转）
    paste_in_area(invoice_rgb, layout['invoice_area'])
    paste_in_area(buy_rgb, layout['buy_area'])
    paste_in_area(pay_rgb, layout['pay_area'])
    
    # 保存成 PDF
    buf = BytesIO()
    canvas_img.save(buf, format="PDF", resolution=dpi)
    data = buf.getvalue()
    buf.close()
    return data


def merge_to_output(src_pdf_path: str, buy_img_path: str, pay_img_path: str, out_pdf_path: str) -> None:
    """渲染发票第一页为图片，与两张记录图一起合成单页 PDF 输出。"""
    inv_img = render_invoice_first_page_as_image(src_pdf_path, dpi=300)
    page_bytes = make_single_page_pdf(inv_img, buy_img_path, pay_img_path)
    with open(out_pdf_path, "wb") as f:
        f.write(page_bytes)


def main(argv: list[str]) -> int:
    # 默认在脚本所在目录运行
    root = os.path.dirname(os.path.abspath(__file__))
    out_dir = ensure_output_dir(root)

    index = build_index(root)

    total_candidates = 0
    total_generated = 0

    for base, items in sorted(index.items()):
        pdf_path = items.get("pdf")
        buy_path = items.get("buy")
        pay_path = items.get("pay")

        # 必须三者齐全
        if not (pdf_path and buy_path and pay_path):
            continue

        total_candidates += 1

        out_name = f"{base}已合并.pdf"
        out_path = os.path.join(out_dir, out_name)

        if os.path.exists(out_path):
            debug(f"跳过（已存在）：{out_name}")
            continue

        try:
            merge_to_output(pdf_path, buy_path, pay_path, out_path)
            total_generated += 1
            debug(f"生成完成：{out_name}")
        except Exception as e:
            debug(f"失败：{base} -> {e}")

    debug("\n统计：")
    debug(f"候选（齐全三件套）: {total_candidates}")
    debug(f"本次新生成: {total_generated}")
    debug(f"输出目录: {out_dir}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))