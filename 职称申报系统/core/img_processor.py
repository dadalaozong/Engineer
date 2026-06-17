"""图像处理模块 — 本地处理（Pillow/OpenCV）+ 第三方API（remove.bg / Clipdrop）。"""
from __future__ import annotations
from pathlib import Path
import base64, requests


# ── 本地处理（无需API Key）────────────────────────────────────────

def enhance_scan(input_path: str, output_path: str | None = None) -> str:
    """提升扫描件质量：灰度化 + 对比度增强 + 锐化。"""
    try:
        from PIL import Image, ImageEnhance, ImageFilter
    except ImportError:
        raise RuntimeError("请安装 Pillow：pip install Pillow")

    img = Image.open(input_path).convert("L")          # 灰度
    img = ImageEnhance.Contrast(img).enhance(1.8)      # 对比度
    img = img.filter(ImageFilter.SHARPEN)               # 锐化

    out = output_path or _auto_output(input_path, "_enhanced")
    img.save(out)
    return out


def deskew(input_path: str, output_path: str | None = None) -> str:
    """自动纠偏倾斜扫描件（需要 opencv-python）。"""
    try:
        import cv2, numpy as np
    except ImportError:
        raise RuntimeError("请安装 opencv-python：pip install opencv-python numpy")

    img  = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
    blur = cv2.GaussianBlur(img, (9, 9), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(thresh > 0))
    angle  = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M      = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h),
                              flags=cv2.INTER_CUBIC,
                              borderMode=cv2.BORDER_REPLICATE)
    out = output_path or _auto_output(input_path, "_deskewed")
    cv2.imwrite(out, rotated)
    return out


# ── remove.bg API ─────────────────────────────────────────────────

def remove_background(input_path: str, api_key: str, output_path: str | None = None) -> str:
    """调用 remove.bg API 去除背景（证件照换底色适用）。"""
    if not api_key:
        raise ValueError("remove.bg API Key 未配置")
    with open(input_path, "rb") as f:
        resp = requests.post(
            "https://api.remove.bg/v1.0/removebg",
            files={"image_file": f},
            data={"size": "auto"},
            headers={"X-Api-Key": api_key},
            timeout=30,
        )
    if resp.status_code != 200:
        raise RuntimeError(f"remove.bg 请求失败 ({resp.status_code}): {resp.text[:200]}")
    out = output_path or _auto_output(input_path, "_nobg", ".png")
    Path(out).write_bytes(resp.content)
    return out


# ── Clipdrop API ──────────────────────────────────────────────────

def upscale_image(input_path: str, api_key: str, output_path: str | None = None) -> str:
    """调用 Clipdrop API 超分辨率放大图片（2×）。"""
    if not api_key:
        raise ValueError("Clipdrop API Key 未配置")
    with open(input_path, "rb") as f:
        resp = requests.post(
            "https://clipdrop-api.co/image-upscaling/v1/upscale",
            files={"image_file": (Path(input_path).name, f, "image/jpeg")},
            data={"target_width": 2048, "target_height": 2048},
            headers={"x-api-key": api_key},
            timeout=60,
        )
    if resp.status_code != 200:
        raise RuntimeError(f"Clipdrop 请求失败 ({resp.status_code}): {resp.text[:200]}")
    out = output_path or _auto_output(input_path, "_upscaled")
    Path(out).write_bytes(resp.content)
    return out


# ── 阿里云图像增强 ────────────────────────────────────────────────

def aliyun_enhance(input_path: str, api_key: str, output_path: str | None = None) -> str:
    """调用阿里云图像增强 API（老照片修复 / 超分辨率）。"""
    if not api_key:
        raise ValueError("阿里云 API Key 未配置")
    with open(input_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    resp = requests.post(
        "https://imageenhan.cn-shanghai.aliyuncs.com",
        json={"imageURL": f"data:image/jpeg;base64,{b64}"},
        headers={
            "Authorization": f"APPCODE {api_key}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"阿里云请求失败 ({resp.status_code}): {resp.text[:200]}")
    result_url = resp.json().get("Data", {}).get("ImageURL", "")
    if not result_url:
        raise RuntimeError("阿里云返回结果为空")
    img_resp = requests.get(result_url, timeout=30)
    out = output_path or _auto_output(input_path, "_aliyun")
    Path(out).write_bytes(img_resp.content)
    return out


# ── helpers ───────────────────────────────────────────────────────

def _auto_output(input_path: str, suffix: str, ext: str | None = None) -> str:
    p = Path(input_path)
    return str(p.parent / f"{p.stem}{suffix}{ext or p.suffix}")
