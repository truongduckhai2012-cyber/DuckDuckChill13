#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Renderer Module
=====================
Ghép phụ đề cứng (hardcode subtitles) và lồng tiếng vào video sử dụng FFmpeg.
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import List, Optional, NamedTuple
from .transcriber import Segment


class RenderResult(NamedTuple):
    success: bool
    output_path: Optional[str] = None
    error: Optional[str] = None


class VideoRenderer:
    """Quản lý render video cuối cùng bằng FFmpeg."""

    def __init__(self, subtitle_style: str = "default", logger: logging.Logger = None):
        self.subtitle_style = subtitle_style
        self.logger = logger or logging.getLogger("VideoRenderer")

    def _get_subtitle_filter(self, srt_path: str) -> str:
        """Tạo cấu hình style cho phụ đề khi ép cứng vào video."""
        # Escape đường dẫn cho ffmpeg filter trên windows/linux
        escaped_path = srt_path.replace("\\", "/").replace(":", "\\:")
        
        styles = {
            "minimal": "FontName=Arial,FontSize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=4",
            "fancy": "FontName=Arial,FontSize=24,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=3,Bold=1",
            "large": "FontName=Arial,FontSize=28,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Bold=1",
            "default": "FontName=Arial,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1"
        }
        style_str = styles.get(self.subtitle_style, styles["default"])
        return f"subtitles='{escaped_path}':force_style='{style_str}'"

    def render(
        self,
        video_path: str,
        output_path: str,
        subtitle_segments: Optional[List[Segment]] = None,
        dubbed_audio_path: Optional[str] = None,
        subtitle_only: bool = False,
        dub_only: bool = False,
        temp_dir: str = "temp"
    ) -> RenderResult:
        """Thực hiện render video hoàn chỉnh."""
        try:
            self.logger.info("🎬 Đang tiến hành render video bằng FFmpeg...")
            temp_path = Path(temp_dir)
            temp_path.mkdir(parents=True, exist_ok=True)

            # Tạo file SRT tạm nếu có subtitle
            srt_path = None
            if subtitle_segments and not dub_only:
                srt_path = temp_path / "render_sub.srt"
                from .transcriber import TranscriptionResult
                res = TranscriptionResult(segments=subtitle_segments, language="vi", text="", duration=0, success=True)
                res.save_srt(str(srt_path))

            # Xây dựng câu lệnh FFmpeg
            cmd = ["ffmpeg", "-y", "-i", video_path]

            if dubbed_audio_path and not subtitle_only:
                cmd.extend(["-i", dubbed_audio_path])

            # Xử lý filter phức hợp (video filter & audio mapping)
            filter_complex = []
            v_label = "0:v"

            # 1. Chèn phụ đề cứng nếu có
            if srt_path and not dub_only:
                sub_filter = self._get_subtitle_filter(str(srt_path))
                filter_complex.append(f"[{v_label}]{sub_filter}[v_out]")
                v_label = "v_out"

            # 2. Xử lý âm thanh (thay thế audio gốc bằng audio lồng tiếng nếu có)
            if dubbed_audio_path and not subtitle_only:
                # Dùng audio từ input 1, giữ video từ v_label
                cmd.extend([
                    "-map", f"[{v_label}]" if v_label != "0:v" else "0:v",
                    "-map", "1:a",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                    "-c:a", "aac", "-b:a", "192k",
                    "-shortest", output_path
                ])
            else:
                # Chỉ có sub hoặc giữ nguyên audio gốc
                if v_label != "0:v":
                    cmd.extend([
                        "-filter_complex", f"[{v_label}]",
                        "-c:a", "copy",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                        output_path
                    ])
                else:
                    # Không làm gì ngoài copy
                    cmd.extend([
                        "-c", "copy",
                        output_path
                    ])

            if filter_complex and (not dubbed_audio_path or subtitle_only):
                # Chèn filter_complex nếu chỉ có video filter
                # Sửa lại cmd cho chuẩn filter_complex
                cmd = ["ffmpeg", "-y", "-i", video_path]
                if srt_path:
                    sub_filter = self._get_subtitle_filter(str(srt_path))
                    cmd.extend(["-vf", sub_filter])
                cmd.extend(["-c:a", "copy", "-c:v", "libx264", "-preset", "medium", "-crf", "20", output_path])

            self.logger.info(f"Đang chạy lệnh FFmpeg...")
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if result.returncode != 0:
                err_msg = result.stderr.decode('utf-8', errors='ignore')
                self.logger.error(f"FFmpeg lỗi: {err_msg}")
                return RenderResult(success=False, error=err_msg)

            self.logger.info(f"✅ Render thành công: {output_path}")
            return RenderResult(success=True, output_path=output_path)

        except Exception as e:
            self.logger.error(f"Lỗi render video: {e}")
            return RenderResult(success=False, error=str(e))

    def extract_subtitle_only(self, segments: List[Segment], output_srt: str):
        """Xuất file phụ đề SRT riêng biệt."""
        from .transcriber import TranscriptionResult
        res = TranscriptionResult(segments=segments, language="vi", text="", duration=0, success=True)
        res.save_srt(output_srt)