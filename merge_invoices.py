#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
发票合并脚本

功能：
- 扫描当前目录，找到形如 “[编号+名称+价格].pdf” 的源发票，以及对应的 “购买记录” 与 “支付记录” 图片（jpg/jpeg/png）。
- 仅当三者齐全时，生成合并后的 PDF 到子目录 “已合并/”，命名为 “[原名]已合并.pdf”。
- 已存在的合并文件不覆盖。
- 不修改任何源文件。

合并规则（单页）：
- A4 纵向白底，四边 30mm 大边距；
- 上半页：源发票（第一页）等比缩放居中；
- 下半页：购买记录、支付记录两张图左右并排，各占四分之一面积，等比缩放居中。

注意：若源发票 PDF 含多页，仅取第一页参与合并。
"""

from __future__ import annotations

import os
import sys
from io import BytesIO
from typing import Dict, Optional, Tuple

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
    base_key 为不含后缀的“编号+名称+价格”原始基名
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
    """使用 Pillow 生成最终单页 PDF（A4 纵向、白底），上半放发票，
    下半左右放购买记录与支付记录。四边大边距 30mm。
    """
    a4_w_mm, a4_h_mm = 210.0, 297.0
    margin_mm = 15.0  # 大边距
    dpi = 300

    def mm_to_px(mm: float) -> int:
        return int(round(mm / 25.4 * dpi))

    page_w = mm_to_px(a4_w_mm)
    page_h = mm_to_px(a4_h_mm)
    margin = mm_to_px(margin_mm)

    # 内容区域尺寸
    content_w = page_w - margin * 2
    content_h = page_h - margin * 2

    # 区域划分
    top_h = content_h // 2        # 上半给发票
    bottom_h = content_h - top_h  # 下半给两张记录图
    col_w = content_w // 2        # 下半左右两列

    # 画布
    canvas_img = Image.new("RGB", (page_w, page_h), color=(255, 255, 255))

    def open_as_rgb(path: str) -> Image.Image:
        img = Image.open(path)
        return img.convert("RGB")

    def fit_into(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
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

    # 准备三张图
    invoice_img = fit_into(invoice_img.convert("RGB"), content_w, top_h)
    buy_img = fit_into(open_as_rgb(buy_img_path), col_w, bottom_h)
    pay_img = fit_into(open_as_rgb(pay_img_path), col_w, bottom_h)

    # 图像坐标：左上(0,0)，向下为正
    # 上半区域顶端：margin
    top_region_top = margin
    # 下半区域顶端：margin + top_h
    bottom_region_top = margin + top_h

    # 将像素坐标系统一为从上往下增长
    def paste_center_topdown(img: Image.Image, region_left: int, region_top: int, region_w: int, region_h: int) -> None:
        w, h = img.size
        x = region_left + (region_w - w) // 2
        y = region_top + (region_h - h) // 2
        canvas_img.paste(img, (x, y))

    # 粘贴上半发票（整行居中）
    paste_center_topdown(invoice_img, margin, top_region_top, content_w, top_h)

    # 下半左右两张
    left_region_left = margin
    right_region_left = margin + col_w
    paste_center_topdown(buy_img, left_region_left, bottom_region_top, col_w, bottom_h)
    paste_center_topdown(pay_img, right_region_left, bottom_region_top, col_w, bottom_h)

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
