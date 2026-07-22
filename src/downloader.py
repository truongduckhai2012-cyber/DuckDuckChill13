#!/usr/init/env python3
# -*- coding: utf-8 -*-
"""
Video Downloader Module
=======================
Tải video và tách âm thanh từ URL hoặc file local sử dụng yt-dlp.
"""

import os
import logging
from pathlib import Path
from typing import NamedTuple, Optional

try:
    import yt_dlp
except ImportError:
    yt_dlp = None


class DownloadResult(NamedTuple):
    success: bool
    video_path: Optional[str] = None
    audio_path: Optional[str] = None
    title: Optional[str] = None
    duration: Optional[float] = 0.0
    error: Optional[str] = None


class VideoDownloader:
    """Quản lý việc tải video và trích xuất audio từ YouTube, TikTok, Facebook, v.v."""

    def __init__(
        self,
        download_dir: str = "downloads",
        temp_dir: str = "temp",
        video_quality: str = "best[height<=1080]",
        audio_quality: str = "bestaudio/best",
        logger: logging.Logger = None
    ):
        self.download_dir = Path(download_dir)
        self.temp_dir = Path(temp_dir)
        self.video_quality = video_quality
        self.audio_quality = audio_quality
        self.logger = logger or logging.getLogger("Downloader")

        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def download(self, url_or_path: str, skip_download: bool = False) -> DownloadResult:
        """Tải video từ URL hoặc kiểm tra file local."""
        # Kiểm tra nếu là file local
        if os.path.exists(url_or_path):
            self.logger.info(f"📂 Phát hiện file local: {url_or_path}")
            video_path = Path(url_or_path)
            title = video_path.stem
            
            # Trích xuất audio từ file local bằng ffmpeg
            audio_path = self.temp_dir / f"{title}_extracted.wav"
            import subprocess
            cmd = [
                "ffmpeg", "-y", "-i", str(video_path),
                "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                str(audio_path)
            ]
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except Exception as e:
                return DownloadResult(success=False, error=f"Lỗi tách audio từ file local: {e}")

            return DownloadResult(
                success=True,
                video_path=str(video_path),
                audio_path=str(audio_path),
                title=title,
                duration=0.0
            )

        if not yt_dlp:
            return DownloadResult(success=False, error="Thư viện yt-dlp chưa được cài đặt.")

        self.logger.info(f"📥 Đang tải video từ URL: {url_or_path}")

        ydl_opts = {
            'format': f'{self.video_quality}+' + f'{self.audio_quality}/best',
            'cookiefile': 'cookies.txt',
            'outtmpl': str(self.download_dir / '%(id)s.%(ext)s'),
            'restrictfilenames': True,
            'noplaylist': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url_or_path, download=True)
                video_id = info.get('id', 'video')
                ext = info.get('ext', 'mp4')
                title = info.get('title', video_id)
                duration = info.get('duration', 0.0)

                video_path = self.download_dir / f"{video_id}.{ext}"
                if not video_path.exists():
                    # Thử tìm file theo định dạng khác nếu tên khác
                    matches = list(self.download_dir.glob(f"{video_id}.*"))
                    if matches:
                        video_path = matches[0]

                # Trích xuất audio chuẩn cho Whisper (WAV 16kHz, mono)
                audio_path = self.temp_dir / f"{video_id}.wav"
                import subprocess
                cmd = [
                    "ffmpeg", "-y", "-i", str(video_path),
                    "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                    str(audio_path)
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                return DownloadResult(
                    success=True,
                    video_path=str(video_path),
                    audio_path=str(audio_path),
                    title=title,
                    duration=float(duration)
                )

        except Exception as e:
            self.logger.error(f"💥 Lỗi tải video: {e}")
            return DownloadResult(success=False, error=str(e))