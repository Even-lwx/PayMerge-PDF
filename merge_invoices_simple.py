#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化版发票合并函数
不依赖文件名，直接接受三个文件路径进行合并
"""

from io import BytesIO
from PIL import Image
import pypdfium2 as pdfium
from typing import Tuple, Dict, Any


def render_pdf_first_page(pdf_path: str, dpi: int = 300) -> Image.Image:
    """渲染PDF第一页为图片"""
    scale = dpi / 72.0
    pdf = pdfium.PdfDocument(pdf_path)
    try:
        if len(pdf) == 0:
            raise ValueError(f"PDF文件无页面: {pdf_path}")
        page = pdf[0]
        try:
            bitmap = page.render(scale=scale)
            img = bitmap.to_pil()
        finally:
            page.close()
    finally:
        pdf.close()
    return img.convert("RGB")


def create_merged_pdf(invoice_img: Image.Image, img1_path: str, img2_path: str) -> bytes:
    """创建合并后的PDF"""
    # A4纸张设置
    a4_w_mm, a4_h_mm = 210.0, 297.0
    margin_mm = 15.0
    dpi = 300

    def mm_to_px(mm: float) -> int:
        return int(round(mm / 25.4 * dpi))

    page_w = mm_to_px(a4_w_mm)
    page_h = mm_to_px(a4_h_mm)
    margin = mm_to_px(margin_mm)

    content_w = page_w - margin * 2
    content_h = page_h - margin * 2

    # 创建白色画布
    canvas_img = Image.new("RGB", (page_w, page_h), color=(255, 255, 255))

    def open_as_rgb(path: str) -> Image.Image:
        img = Image.open(path)
        return img.convert("RGB")

    def fit_into(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
        """等比缩放图片"""
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

    def get_optimal_layout(invoice_size: Tuple[int, int], img1_size: Tuple[int, int], img2_size: Tuple[int, int]) -> Dict[str, Any]:
        """计算最优布局，考虑旋转可能性"""
        best_layout = None
        best_score = 0
        best_orientations = {}

        # 测试所有旋转组合
        for inv_rot in [False, True]:
            for img1_rot in [False, True]:
                for img2_rot in [False, True]:

                    # 计算旋转后的尺寸
                    inv_w, inv_h = invoice_size if not inv_rot else (invoice_size[1], invoice_size[0])
                    img1_w, img1_h = img1_size if not img1_rot else (img1_size[1], img1_size[0])
                    img2_w, img2_h = img2_size if not img2_rot else (img2_size[1], img2_size[0])

                    # 计算宽高比
                    inv_ratio = inv_w / inv_h
                    img1_ratio = img1_w / img1_h
                    img2_ratio = img2_w / img2_h

                    # 方案1: 发票在上，两图片并排在下
                    max_inv_h_1 = min(content_h * 0.65, content_w / inv_ratio)
                    inv_scale_1 = min(content_w / inv_w, max_inv_h_1 / inv_h)
                    actual_inv_h_1 = int(inv_h * inv_scale_1)

                    remaining_h_1 = content_h - actual_inv_h_1 - mm_to_px(5)
                    if remaining_h_1 > 0:
                        total_width_ratio = img1_ratio + img2_ratio
                        img1_area_w_1 = int(content_w * (img1_ratio / total_width_ratio))
                        img2_area_w_1 = content_w - img1_area_w_1

                        img1_scale_1 = min(img1_area_w_1 / img1_w, remaining_h_1 / img1_h)
                        img2_scale_1 = min(img2_area_w_1 / img2_w, remaining_h_1 / img2_h)
                    else:
                        img1_scale_1 = img2_scale_1 = 0

                    layout_1_score = inv_scale_1 + img1_scale_1 + img2_scale_1

                    # 方案2: 发票在左，两图片纵向排列在右
                    max_inv_w_2 = min(content_w * 0.6, content_h * inv_ratio)
                    inv_scale_2 = min(max_inv_w_2 / inv_w, content_h / inv_h)
                    actual_inv_w_2 = int(inv_w * inv_scale_2)

                    remaining_w_2 = content_w - actual_inv_w_2 - mm_to_px(5)
                    if remaining_w_2 > 0:
                        each_h_2 = content_h // 2
                        img1_scale_2 = min(remaining_w_2 / img1_w, each_h_2 / img1_h)
                        img2_scale_2 = min(remaining_w_2 / img2_w, each_h_2 / img2_h)
                    else:
                        img1_scale_2 = img2_scale_2 = 0

                    layout_2_score = inv_scale_2 + img1_scale_2 + img2_scale_2

                    # 选择最佳布局
                    if layout_1_score >= layout_2_score:
                        current_score = layout_1_score
                        current_layout = {
                            'type': 'horizontal',
                            'invoice_area': (0, 0, content_w, actual_inv_h_1),
                            'img1_area': (0, actual_inv_h_1 + mm_to_px(5), img1_area_w_1, remaining_h_1),
                            'img2_area': (img1_area_w_1, actual_inv_h_1 + mm_to_px(5), img2_area_w_1, remaining_h_1)
                        }
                    else:
                        current_score = layout_2_score
                        current_layout = {
                            'type': 'vertical',
                            'invoice_area': (0, 0, actual_inv_w_2, content_h),
                            'img1_area': (actual_inv_w_2 + mm_to_px(5), 0, remaining_w_2, each_h_2),
                            'img2_area': (actual_inv_w_2 + mm_to_px(5), each_h_2, remaining_w_2, each_h_2)
                        }

                    # 更新全局最佳方案
                    if current_score > best_score:
                        best_score = current_score
                        best_layout = current_layout
                        best_orientations = {
                            'invoice_rotate': inv_rot,
                            'img1_rotate': img1_rot,
                            'img2_rotate': img2_rot
                        }

        best_layout['orientations'] = best_orientations
        return best_layout

    # 准备图片
    invoice_rgb = invoice_img.convert("RGB")
    img1_rgb = open_as_rgb(img1_path)
    img2_rgb = open_as_rgb(img2_path)

    # 计算最优布局
    layout = get_optimal_layout(invoice_rgb.size, img1_rgb.size, img2_rgb.size)
    orientations = layout['orientations']

    # 根据最优方案旋转图片
    if orientations['invoice_rotate']:
        invoice_rgb = invoice_rgb.rotate(90, expand=True)

    if orientations['img1_rotate']:
        img1_rgb = img1_rgb.rotate(90, expand=True)

    if orientations['img2_rotate']:
        img2_rgb = img2_rgb.rotate(90, expand=True)

    def paste_in_area(img: Image.Image, area: Tuple[int, int, int, int]) -> None:
        """在指定区域内居中粘贴图片"""
        area_x, area_y, area_w, area_h = area
        fitted_img = fit_into(img, area_w, area_h)

        # 计算居中位置
        img_w, img_h = fitted_img.size
        x = margin + area_x + (area_w - img_w) // 2
        y = margin + area_y + (area_h - img_h) // 2

        canvas_img.paste(fitted_img, (x, y))

    # 粘贴三张图片
    paste_in_area(invoice_rgb, layout['invoice_area'])
    paste_in_area(img1_rgb, layout['img1_area'])
    paste_in_area(img2_rgb, layout['img2_area'])

    # 保存为PDF
    buf = BytesIO()
    canvas_img.save(buf, format="PDF", resolution=dpi)
    data = buf.getvalue()
    buf.close()
    return data


def merge_simple(pdf_path: str, img1_path: str, img2_path: str, output_path: str) -> None:
    """
    简单的合并函数，不依赖文件名

    Args:
        pdf_path: PDF发票路径
        img1_path: 第一张图片路径（购买记录）
        img2_path: 第二张图片路径（支付记录）
        output_path: 输出PDF路径
    """
    # 渲染PDF第一页
    invoice_img = render_pdf_first_page(pdf_path, dpi=300)

    # 创建合并后的PDF
    pdf_data = create_merged_pdf(invoice_img, img1_path, img2_path)

    # 保存到文件
    with open(output_path, "wb") as f:
        f.write(pdf_data)

    print(f"✅ 合并完成：{output_path}")