#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Video Translation & Dubbing Tool
===================================
Main entry point for command-line interface.
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Thêm thư mục hiện tại vào path để import các module trong src
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.pipeline import VideoTranslationPipeline
from src.utils import setup_logger
from config import (
    DEFAULT_SOURCE_LANG, DEFAULT_TARGET_LANG, DEFAULT_WHISPER_MODEL,
    DEFAULT_TRANSLATE_ENGINE, DEFAULT_SUBTITLE_STYLE, DEFAULT_VIDEO_QUALITY,
    DEFAULT_AUDIO_QUALITY, DEFAULT_OUTPUT_DIR, DEFAULT_TEMP_DIR,
    DEFAULT_DOWNLOAD_DIR, OPENAI_API_KEY, DEEPSEEK_API_KEY
)


def parse_arguments():
    """Phân tích các tham số dòng lệnh."""
    parser = argparse.ArgumentParser(
        description="🎬 AI Video Translation & Dubbing Tool - Tự động dịch và lồng tiếng video",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  # Dịch video YouTube sang Tiếng Việt (mặc định)
  python main.py -u "https://www.youtube.com/watch?v=VIDEO_ID"

  # Chỉ tạo phụ đề, không lồng tiếng
  python main.py -u "https://youtu.be/VIDEO_ID" -s en -t vi --subtitle-only

  # Dịch bằng OpenAI GPT chất lượng cao
  python main.py -u "video.mp4" -s en -t vi --translate-engine openai --openai-api-key "sk-..."
        """
    )

    # Bắt buộc
    parser.add_argument(
        "-u", "--url",
        required=True,
        help="Link video (YouTube, TikTok, Facebook,...) hoặc đường dẫn file local"
    )

    # Ngôn ngữ
    parser.add_argument(
        "-s", "--source-lang",
        default=DEFAULT_SOURCE_LANG,
        help=f"Ngôn ngữ nguồn (auto/en/vi/ja/ko/zh/...) [default: {DEFAULT_SOURCE_LANG}]"
    )
    parser.add_argument(
        "-t", "--target-lang",
        default=DEFAULT_TARGET_LANG,
        help=f"Ngôn ngữ đích [default: {DEFAULT_TARGET_LANG}]"
    )

    # Chế độ
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--subtitle-only",
        action="store_true",
        help="Chỉ tạo và chèn phụ đề (không lồng tiếng)"
    )
    mode_group.add_argument(
        "--dub-only",
        action="store_true",
        help="Chỉ lồng tiếng (không chèn phụ đề)"
    )

    # AI Models & Engines
    parser.add_argument(
        "--whisper-model",
        default=DEFAULT_WHISPER_MODEL,
        choices=["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"],
        help=f"Mô hình Whisper cho STT [default: {DEFAULT_WHISPER_MODEL}]"
    )
    parser.add_argument(
        "--translate-engine",
        default=DEFAULT_TRANSLATE_ENGINE,
        choices=["google", "openai", "deepseek"],
        help=f"Engine dịch thuật [default: {DEFAULT_TRANSLATE_ENGINE}]"
    )
    parser.add_argument(
        "--tts-voice",
        default=None,
        help="Giọng Edge-TTS cụ thể (ví dụ: vi-VN-NamMinhNeural, vi-VN-HoaiMyNeural)"
    )
    parser.add_argument(
        "--subtitle-style",
        default=DEFAULT_SUBTITLE_STYLE,
        choices=["default", "minimal", "fancy", "large"],
        help=f"Phong cách hiển thị phụ đề [default: {DEFAULT_SUBTITLE_STYLE}]"
    )

    # Chất lượng & Thư mục
    parser.add_argument(
        "--video-quality",
        default=DEFAULT_VIDEO_QUALITY,
        help=f"Chất lượng video yt-dlp [default: {DEFAULT_VIDEO_QUALITY}]"
    )
    parser.add_argument(
        "--audio-quality",
        default=DEFAULT_AUDIO_QUALITY,
        help=f"Chất lượng âm thanh yt-dlp [default: {DEFAULT_AUDIO_QUALITY}]"
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Thư mục lưu kết quả [default: {DEFAULT_OUTPUT_DIR}]"
    )
    parser.add_argument(
        "--temp-dir",
        default=DEFAULT_TEMP_DIR,
        help=f"Thư mục file tạm [default: {DEFAULT_TEMP_DIR}]"
    )
    parser.add_argument(
        "--download-dir",
        default=DEFAULT_DOWNLOAD_DIR,
        help=f"Thư mục tải video [default: {DEFAULT_DOWNLOAD_DIR}]"
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Giữ lại file tạm sau khi xử lý xong"
    )

    # API Keys
    parser.add_argument(
        "--openai-api-key",
        default=OPENAI_API_KEY,
        help="OpenAI API Key"
    )
    parser.add_argument(
        "--deepseek-api-key",
        default=DEEPSEEK_API_KEY,
        help="DeepSeek API Key"
    )

    # Khác
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Hiển thị log chi tiết (DEBUG mode)"
    )

    return parser.parse_args()


def main():
    args = parse_arguments()

    # Thiết lập Logger
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logger("VideoTranslator", level=log_level)

    logger.info("🎬 Bắt đầu chạy công cụ Dịch & Lồng tiếng Video AI")

    # Khởi tạo Pipeline
    pipeline = VideoTranslationPipeline(
        source_lang=args.source_lang,
        target_lang=args.target_lang,
        whisper_model=args.whisper_model,
        tts_voice=args.tts_voice,
        subtitle_style=args.subtitle_style,
        translate_engine=args.translate_engine,
        openai_api_key=args.openai_api_key,
        deepseek_api_key=args.deepseek_api_key,
        video_quality=args.video_quality,
        audio_quality=args.audio_quality,
        output_dir=args.output_dir,
        temp_dir=args.temp_dir,
        download_dir=args.download_dir,
        keep_temp=args.keep_temp,
        verbose=args.verbose,
        logger=logger
    )

    # Chạy pipeline
    result = pipeline.run(
        url=args.url,
        subtitle_only=args.subtitle_only,
        dub_only=args.dub_only,
        skip_download=False
    )

    if result["success"]:
        logger.info(f"✨ Xử lý thành công! File xuất ra tại: {result['output_path']}")
        sys.exit(0)
    else:
        logger.error(f"❌ Xử lý thất bại: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()