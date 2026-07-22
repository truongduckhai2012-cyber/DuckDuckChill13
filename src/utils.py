#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilities Module
================
Các hàm tiện ích dùng chung cho toàn bộ dự án.
"""

import os
import re
import shutil
import logging
from pathlib import Path
from typing import Optional


def setup_logger(name: str = "VideoTranslator", level: int = logging.INFO) -> logging.Logger:
    """Thiết lập và trả về Logger cấu hình chuẩn màu sắc, định dạng."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger


def ensure_dir(dir_path: str) -> Path:
    """Đảm bảo thư mục tồn tại, nếu chưa có thì tạo mới."""
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_safe_filename(title: str, default_ext: str = "mp4") -> str:
    """Chuyển đổi tiêu đề video thành tên file an toàn với hệ điều hành."""
    # Loại bỏ ký tự đặc biệt
    safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
    safe_title = safe_title.strip()
    if not safe_title:
        safe_title = "video_output"
    return f"{safe_title[:100]}.{default_ext}"


def get_language_name(lang_code: str) -> str:
    """Lấy tên ngôn ngữ đầy đủ từ mã code."""
    languages = {
        "auto": "Tự động nhận diện",
        "vi": "Tiếng Việt",
        "en": "English",
        "ja": "日本語 (Nhật)",
        "ko": "한국어 (Hàn)",
        "zh": "中文 (Trung)",
        "fr": "Français (Pháp)",
        "de": "Deutsch (Đức)",
        "es": "Español (Tây Ban Nha)",
        "ru": "Русский (Nga)",
        "pt": "Português (Bồ Đào Nha)",
        "ar": "العربية (Ả Rập)",
        "hi": "हिन्दी (Ấn Độ)",
        "th": "ไทย (Thái Lan)",
        "id": "Bahasa Indonesia",
        "ms": "Bahasa Melayu",
        "tl": "Tagalog (Philippines)",
        "it": "Italiano (Ý)",
        "tr": "Türkçe (Thổ Nhĩ Kỳ)",
        "pl": "Polski (Ba Lan)",
        "nl": "Nederlands (Hà Lan)"
    }
    return languages.get(lang_code.lower(), lang_code)


class ProgressTracker:
    """Theo dõi tiến độ các bước thực hiện trong Pipeline."""
    def __init__(self, total_steps: int = 7):
        self.current_step = 0
        self.total_steps = total_steps

    def next_step(self, description: str):
        self.current_step += 1
        print(f"\n[Bước {self.current_step}/{self.total_steps}] {description}")
        print("-" * 50)

    def finish(self):
        print("\n" + "=" * 50)
        print("🎉 Hoàn thành tất cả các bước xử lý!")
        print("=" * 50)


def cleanup_temp_files(temp_dir: str, keep: bool = False, logger: logging.Logger = None):
    """Dọn dẹp các file tạm trong thư mục temp."""
    if keep:
        return
    path = Path(temp_dir)
    if path.exists():
        if logger:
            logger.info(f"🧹 Đang dọn dẹp thư mục tạm: {temp_dir}")
        for item in path.glob('*'):
            try:
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            except Exception as e:
                if logger:
                    logger.warning(f"Không thể xóa {item}: {e}")
def is_youtube_url(url: str) -> bool:
    return any(domain in url for domain in ["youtube.com", "youtu.be", "m.youtube.com"])

def is_tiktok_url(url: str) -> bool:
    return "tiktok.com" in url

def is_facebook_url(url: str) -> bool:
    return any(domain in url for domain in ["facebook.com", "fb.watch", "fb.com"])                                        