#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module 1: Download & Extract
============================
Tải video đa nền tảng tối ưu cho ứng dụng web (không cần cookies/đăng nhập).
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

from .utils import ensure_dir, get_safe_filename, is_youtube_url, is_tiktok_url, is_facebook_url


@dataclass
class DownloadResult:
    """Kết quả tải video."""
    video_path: str
    audio_path: str
    title: str
    duration: float
    uploader: str
    resolution: str
    success: bool
    error: Optional[str] = None


class VideoDownloader:
    """Trình tải video đa nền tảng sử dụng yt-dlp và FFmpeg."""
    
    def __init__(
        self,
        download_dir: str = "downloads",
        temp_dir: str = "temp",
        video_quality: str = "bestvideo+bestaudio/best",
        audio_quality: str = "bestaudio/best",
        logger: logging.Logger = None
    ):
        self.download_dir = ensure_dir(download_dir)
        self.temp_dir = ensure_dir(temp_dir)
        self.video_quality = video_quality
        self.audio_quality = audio_quality
        self.logger = logger or logging.getLogger("VideoDownloader")
        
        self._check_yt_dlp()
        self._check_ffmpeg()
    
    def _check_yt_dlp(self):
        try:
            import yt_dlp
            self.yt_dlp_available = True
        except ImportError:
            raise ImportError("yt-dlp là bắt buộc. Cài đặt: pip install yt-dlp")
    
    def _check_ffmpeg(self):
        try:
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                raise RuntimeError("FFmpeg không hoạt động")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            raise RuntimeError("FFmpeg là bắt buộc.")
    
    def download(self, url: str, skip_download: bool = False) -> DownloadResult:
        self.logger.info(f"🔗 URL: {url}")
        
        if os.path.isfile(url):
            return self._process_local_file(url)
        
        try:
            return self._download_with_yt_dlp(url)
        except Exception as e:
            self.logger.error(f"❌ Lỗi tải video: {e}")
            return DownloadResult(
                video_path="", audio_path="", title="", 
                duration=0, uploader="", resolution="",
                success=False, error=str(e)
            )
    
    def _process_local_file(self, filepath: str) -> DownloadResult:
        filepath = Path(filepath).resolve()
        if not filepath.exists():
            return DownloadResult(
                video_path="", audio_path="", title="", duration=0, 
                uploader="", resolution="", success=False, error="File không tồn tại"
            )
        
        dest_video = self.download_dir / filepath.name
        import shutil
        shutil.copy2(filepath, dest_video)
        audio_path = self._extract_audio(str(dest_video))
        duration = self._get_duration(str(dest_video))
        
        return DownloadResult(
            video_path=str(dest_video), audio_path=audio_path, title=filepath.stem,
            duration=duration, uploader="Local File", resolution="Unknown", success=True
        )
    
    def _download_with_yt_dlp(self, url: str) -> DownloadResult:
        import yt_dlp
        self.logger.info("⬇️  Đang tải video...")
        
        temp_id = f"dl_{os.urandom(4).hex()}"
        output_template = str(self.temp_dir / f"{temp_id}_%(title)s.%(ext)s")
        
        ydl_opts = {
            "format": self.video_quality,
            "outtmpl": output_template,
            "merge_output_format": "mp4",
            "writeinfojson": False,
            "writethumbnail": False,
            "quiet": True,
            "no_warnings": True,
            "extractor_args": {
                "youtube": {
                    "player-client": ["mweb", "web"]
                }
            },
            "postprocessors": [{"key": "FFmpegMetadata", "add_metadata": True}],
        }
        
        if is_tiktok_url(url) or is_facebook_url(url):
            ydl_opts["format"] = "best"
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get("title", "unknown")
                duration = info.get("duration", 0)
                uploader = info.get("uploader", "unknown")
                
                ydl.download([url])
                
                downloaded_files = list(self.temp_dir.glob(f"{temp_id}_*"))
                video_file = next((f for f in downloaded_files if f.suffix in [".mp4", ".webm", ".mkv", ".mov"]), None)
                
                if not video_file:
                    raise RuntimeError("Không tìm thấy file video đã tải.")
                
                safe_name = get_safe_filename(title, "mp4")
                final_video = self.download_dir / safe_name
                
                counter = 1
                while final_video.exists():
                    stem = safe_name.rsplit(".", 1)[0]
                    final_video = self.download_dir / f"{stem}_{counter}.mp4"
                    counter += 1
                
                os.rename(video_file, final_video)
                for f in downloaded_files:
                    if f != video_file and f.exists():
                        f.unlink()
                
                audio_path = self._extract_audio(str(final_video))
                resolution = info.get("resolution", "unknown")
                
                return DownloadResult(
                    video_path=str(final_video), audio_path=audio_path, title=title,
                    duration=duration, uploader=uploader, resolution=resolution, success=True
                )
        except Exception as e:
            self.logger.error(f"Lỗi yt-dlp chính: {e}")
            return self._download_fallback(url, temp_id)
    
    def _download_fallback(self, url: str, temp_id: str) -> DownloadResult:
        import yt_dlp
        self.logger.warning("🔄 Thử phương án tải dự phòng...")
        
        output_template = str(self.temp_dir / f"{temp_id}_fb_%(title)s.%(ext)s")
        ydl_opts = {
            "format": "best",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "extractor_args": {
                "youtube": {
                    "player-client": ["android"]
                }
            }
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get("title", "unknown")
                duration = info.get("duration", 0)
                
                downloaded_files = list(self.temp_dir.glob(f"{temp_id}_fb_*"))
                video_file = next((f for f in downloaded_files if f.suffix in [".mp4", ".webm", ".mkv"]), None)
                
                if not video_file:
                    raise RuntimeError("Không tìm thấy file video.")
                
                safe_name = get_safe_filename(title, "mp4")
                final_video = self.download_dir / safe_name
                
                counter = 1
                while final_video.exists():
                    stem = safe_name.rsplit(".", 1)[0]
                    final_video = self.download_dir / f"{stem}_{counter}.mp4"
                    counter += 1
                
                os.rename(video_file, final_video)
                for f in downloaded_files:
                    if f != video_file and f.exists():
                        f.unlink()
                
                audio_path = self._extract_audio(str(final_video))
                
                return DownloadResult(
                    video_path=str(final_video), audio_path=audio_path, title=title,
                    duration=duration, uploader=info.get("uploader", "unknown"),
                    resolution=info.get("resolution", "unknown"), success=True
                )
        except Exception as e:
            return DownloadResult(
                video_path="", audio_path="", title="", duration=0, uploader="", resolution="",
                success=False, error=f"Tải dự phòng thất bại: {e}"
            )
    
    def _extract_audio(self, video_path: str) -> str:
        audio_path = str(Path(video_path).with_suffix(".wav"))
        cmd = [
            "ffmpeg", "-y", "-i", video_path, "-vn",
            "-acodec", "pcm_s16le", "-ac", "1", "-ar", "16000",
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", audio_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if os.path.exists(audio_path):
            return audio_path
        raise RuntimeError("File âm thanh không được tạo.")
    
    def _get_duration(self, video_path: str) -> float:
        try:
            cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return float(result.stdout.strip())
        except Exception:
            return 0.0