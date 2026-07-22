#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module 1: Download & Extract
============================
Tải video từ YouTube, TikTok, Facebook hoặc link trực tiếp.
Trích xuất âm thanh thành file WAV tối ưu.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

from tqdm import tqdm

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
        
        # Kiểm tra yt-dlp
        self._check_yt_dlp()
        # Kiểm tra FFmpeg
        self._check_ffmpeg()
    
    def _check_yt_dlp(self):
        """Kiểm tra yt-dlp đã cài đặt chưa."""
        try:
            import yt_dlp
            self.yt_dlp_available = True
            self.logger.debug("yt-dlp đã sẵn sàng.")
        except ImportError:
            self.yt_dlp_available = False
            self.logger.error("yt-dlp chưa được cài đặt. Chạy: pip install yt-dlp")
            raise ImportError("yt-dlp là bắt buộc. Cài đặt: pip install yt-dlp")
    
    def _check_ffmpeg(self):
        """Kiểm tra FFmpeg đã cài đặt chưa."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                version_line = result.stdout.split("\n")[0]
                self.logger.debug(f"FFmpeg: {version_line}")
            else:
                raise RuntimeError("FFmpeg không hoạt động")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.logger.error("FFmpeg chưa được cài đặt hoặc không có trong PATH.")
            raise RuntimeError("FFmpeg là bắt buộc. Cài đặt: https://ffmpeg.org/download.html")
    
    def download(self, url: str, skip_download: bool = False) -> DownloadResult:
        """
        Tải video từ URL.
        
        Args:
            url: Link video hoặc đường dẫn file local
            skip_download: Bỏ qua tải nếu là file local
            
        Returns:
            DownloadResult: Kết quả tải video
        """
        self.logger.info(f"🔗 URL: {url}")
        
        # Nếu là file local
        if os.path.isfile(url):
            self.logger.info("📁 Phát hiện file local, bỏ qua tải về.")
            return self._process_local_file(url)
        
        if skip_download:
            self.logger.warning("--no-download được bật nhưng URL không phải file local.")
        
        # Xác định nguồn
        source = self._detect_source(url)
        self.logger.info(f"🌐 Nguồn: {source}")
        
        try:
            return self._download_with_yt_dlp(url)
        except Exception as e:
            self.logger.error(f"❌ Lỗi tải video: {e}")
            return DownloadResult(
                video_path="", audio_path="", title="", 
                duration=0, uploader="", resolution="",
                success=False, error=str(e)
            )
    
    def _detect_source(self, url: str) -> str:
        """Nhận diện nguồn video."""
        if is_youtube_url(url):
            return "YouTube"
        elif is_tiktok_url(url):
            return "TikTok"
        elif is_facebook_url(url):
            return "Facebook"
        else:
            return "Direct Link"
    
    def _process_local_file(self, filepath: str) -> DownloadResult:
        """Xử lý file video local."""
        filepath = Path(filepath).resolve()
        
        if not filepath.exists():
            return DownloadResult(
                video_path="", audio_path="", title="",
                duration=0, uploader="", resolution="",
                success=False, error=f"File không tồn tại: {filepath}"
            )
        
        # Copy vào thư mục downloads
        dest_video = self.download_dir / filepath.name
        import shutil
        shutil.copy2(filepath, dest_video)
        
        # Trích xuất âm thanh
        audio_path = self._extract_audio(str(dest_video))
        
        # Lấy thông tin video
        duration = self._get_duration(str(dest_video))
        
        return DownloadResult(
            video_path=str(dest_video),
            audio_path=audio_path,
            title=filepath.stem,
            duration=duration,
            uploader="Local File",
            resolution="Unknown",
            success=True
        )
    
    def _download_with_yt_dlp(self, url: str) -> DownloadResult:
        """Tải video sử dụng yt-dlp."""
        import yt_dlp
        
        self.logger.info("⬇️  Đang tải video...")
        
        # Tạo tên file tạm
        temp_id = f"dl_{os.urandom(4).hex()}"
        output_template = str(self.temp_dir / f"{temp_id}_%(title)s.%(ext)s")
        
        # Cấu hình yt-dlp tối ưu và bypass bot qua cookiesfrombrowser
        ydl_opts = {
            "format": self.video_quality,
            "outtmpl": output_template,
            "merge_output_format": "mp4",
            "writeinfojson": False,
            "writethumbnail": False,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [self._progress_hook],
            "cookiesfrombrowser": ("chrome",),  # Tự động lấy cookie từ Chrome để chống chặn bot
            "postprocessors": [{
                "key": "FFmpegMetadata",
                "add_metadata": True,
            }],
        }
        
        # Tùy chỉnh cho từng nguồn
        if is_tiktok_url(url):
            ydl_opts["format"] = "best"
        elif is_facebook_url(url):
            ydl_opts["format"] = "best"
        
        info = {}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Lấy thông tin trước
                info = ydl.extract_info(url, download=False)
                title = info.get("title", "unknown")
                duration = info.get("duration", 0)
                uploader = info.get("uploader", "unknown")
                
                self.logger.info(f"📺 Tiêu đề: {title}")
                self.logger.info(f"⏱️  Thời lượng: {duration}s")
                self.logger.info(f"👤 Tác giả: {uploader}")
                
                # Tải video
                ydl.download([url])
                
                # Tìm file đã tải
                downloaded_files = list(self.temp_dir.glob(f"{temp_id}_*"))
                video_file = None
                for f in downloaded_files:
                    if f.suffix in [".mp4", ".webm", ".mkv", ".mov"]:
                        video_file = f
                        break
                
                if not video_file:
                    raise RuntimeError("Không tìm thấy file video đã tải.")
                
                # Di chuyển vào thư mục downloads
                safe_name = get_safe_filename(title, "mp4")
                final_video = self.download_dir / safe_name
                
                # Nếu đã tồn tại, thêm số
                counter = 1
                while final_video.exists():
                    stem = safe_name.rsplit(".", 1)[0]
                    final_video = self.download_dir / f"{stem}_{counter}.mp4"
                    counter += 1
                
                os.rename(video_file, final_video)
                
                # Dọn dẹp file tạm
                for f in downloaded_files:
                    if f != video_file and f.exists():
                        f.unlink()
                
                # Trích xuất âm thanh
                audio_path = self._extract_audio(str(final_video))
                
                # Lấy độ phân giải
                resolution = info.get("resolution", "unknown")
                if not resolution or resolution == "unknown":
                    width = info.get("width", 0)
                    height = info.get("height", 0)
                    if width and height:
                        resolution = f"{width}x{height}"
                
                self.logger.info(f"✅ Tải video thành công: {final_video.name}")
                
                return DownloadResult(
                    video_path=str(final_video),
                    audio_path=audio_path,
                    title=title,
                    duration=duration,
                    uploader=uploader,
                    resolution=resolution,
                    success=True
                )
                
        except Exception as e:
            self.logger.error(f"Lỗi yt-dlp: {e}")
            return self._download_fallback(url, temp_id)
    
    def _download_fallback(self, url: str, temp_id: str) -> DownloadResult:
        """Phương án dự phòng khi tải thất bại."""
        import yt_dlp
        
        self.logger.warning("🔄 Thử phương án tải dự phòng (best quality)...")
        
        output_template = str(self.temp_dir / f"{temp_id}_fb_%(title)s.%(ext)s")
        
        ydl_opts = {
            "format": "best",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "cookiesfrombrowser": ("chrome",),
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get("title", "unknown")
                duration = info.get("duration", 0)
                
                downloaded_files = list(self.temp_dir.glob(f"{temp_id}_fb_*"))
                video_file = None
                for f in downloaded_files:
                    if f.suffix in [".mp4", ".webm", ".mkv"]:
                        video_file = f
                        break
                
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
                    video_path=str(final_video),
                    audio_path=audio_path,
                    title=title,
                    duration=duration,
                    uploader=info.get("uploader", "unknown"),
                    resolution=info.get("resolution", "unknown"),
                    success=True
                )
                
        except Exception as e:
            return DownloadResult(
                video_path="", audio_path="", title="",
                duration=0, uploader="", resolution="",
                success=False, error=f"Tải dự phòng cũng thất bại: {e}"
            )
    
    def _extract_audio(self, video_path: str) -> str:
        """
        Trích xuất âm thanh từ video thành WAV.
        Tối ưu cho Whisper: 16kHz, mono, 16-bit.
        """
        self.logger.info("🔊 Đang trích xuất âm thanh...")
        
        audio_path = str(Path(video_path).with_suffix(".wav"))
        
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ac", "1",
            "-ar", "16000",
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            audio_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                self.logger.warning(f"FFmpeg warning: {result.stderr[:200]}")
            
            if os.path.exists(audio_path):
                size_mb = os.path.getsize(audio_path) / (1024 * 1024)
                self.logger.info(f"✅ Âm thanh: {audio_path} ({size_mb:.1f} MB)")
                return audio_path
            else:
                raise RuntimeError("File âm thanh không được tạo.")
                
        except subprocess.TimeoutExpired:
            raise RuntimeError("Trích xuất âm thanh quá thời gian (>5 phút).")
        except Exception as e:
            raise RuntimeError(f"Lỗi trích xuất âm thanh: {e}")
    
    def _get_duration(self, video_path: str) -> float:
        """Lấy thời lượng video."""
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return float(result.stdout.strip())
        except Exception:
            return 0.0
    
    def _progress_hook(self, d: dict):
        """Hook theo dõi tiến trình tải."""
        if d["status"] == "downloading":
            downloaded = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes", 0) or d.get("total_bytes_estimate", 0)
            if total > 0:
                percent = (downloaded / total) * 100
                speed = d.get("speed", 0)
                speed_str = f"{speed / 1024 / 1024:.1f} MB/s" if speed else "N/A"
                self.logger.debug(f"Tải: {percent:.1f}% | Tốc độ: {speed_str}")
        elif d["status"] == "finished":
            self.logger.info("✅ Tải xuống hoàn tất!")