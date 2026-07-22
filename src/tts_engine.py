#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS Engine Module
=================
Tổng hợp giọng đọc nhân tạo (Text-to-Speech) sử dụng edge-tts.
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import List, NamedTuple, Optional
from .transcriber import Segment


class TTSResult(NamedTuple):
    success: bool
    audio_path: Optional[str] = None
    error: Optional[str] = None


class EdgeTTSEngine:
    """Quản lý tổng hợp giọng đọc từ Microsoft Edge TTS."""

    DEFAULT_VOICES = {
        "vi": "vi-VN-HoaiMyNeural",
        "en": "en-US-AriaNeural",
        "ja": "ja-JP-NanamiNeural",
        "ko": "ko-KR-SunHiNeural",
        "zh": "zh-CN-XiaoxiaoNeural",
        "fr": "fr-FR-DeniseNeural",
        "de": "de-DE-KatjaNeural",
        "es": "es-ES-ElviraNeural",
    }

    def __init__(self, voice: Optional[str] = None, language: str = "vi", logger: logging.Logger = None):
        self.language = language.lower()
        self.voice = voice or self.DEFAULT_VOICES.get(self.language, "vi-VN-HoaiMyNeural")
        self.logger = logger or logging.getLogger("EdgeTTS")

    def synthesize_segments(self, segments: List[Segment], output_dir: str, sync_timing: bool = True) -> TTSResult:
        """Tổng hợp âm thanh cho từng đoạn và ghép nối thành một file audio hoàn chỉnh."""
        try:
            import edge_tts
            import subprocess

            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"🗣️ Đang tổng hợp giọng đọc với Edge-TTS (Giọng: {self.voice})...")

            async def _synth():
                audio_files = []
                for seg in segments:
                    seg_file = out_dir / f"seg_{seg.id:04d}.mp3"
                    communicate = edge_tts.Communicate(seg.text, self.voice)
                    await communicate.save(str(seg_file))
                    audio_files.append((seg, seg_file))
                return audio_files

            # Xử lý an toàn event loop cho cả MainThread và các luồng khác
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                try:
                    import nest_asyncio
                    nest_asyncio.apply()
                except ImportError:
                    pass
                audio_files = loop.run_until_complete(_synth())
            else:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    audio_files = loop.run_until_complete(_synth())
                finally:
                    loop.close()

            # Dùng ffmpeg để căn chỉnh thời gian các đoạn audio khớp với timeline video
            final_audio_path = out_dir / "dubbed_final.wav"
            self.logger.info("🎬 Đang đồng bộ thời gian âm thanh lồng tiếng...")

            concat_list_path = out_dir / "concat_list.txt"
            with open(concat_list_path, "w", encoding="utf-8") as f:
                current_time = 0.0
                for i, (seg, fpath) in enumerate(audio_files):
                    # Thêm khoảng lặng nếu có khoảng trống giữa các đoạn câu
                    if seg.start > current_time:
                        silence_duration = seg.start - current_time
                        sil_path = out_dir / f"silence_{i}.wav"
                        subprocess.run([
                            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono",
                            "-t", str(silence_duration), str(sil_path)
                        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        f.write(f"file '{sil_path.absolute()}'\n")
                    
                    # Chuyển đổi mp3 sang wav chuẩn 16k mono để ghép nối
                    wav_seg_path = out_dir / f"seg_{seg.id:04d}.wav"
                    subprocess.run([
                        "ffmpeg", "-y", "-i", str(fpath), "-ar", "16000", "-ac", "1", str(wav_seg_path)
                    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    f.write(f"file '{wav_seg_path.absolute()}'\n")
                    current_time = seg.end

            # Thực hiện nối toàn bộ các file audio bằng FFmpeg concat demuxer
            subprocess.run([
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", str(concat_list_path), "-c:a", "pcm_s16le", str(final_audio_path)
            ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            self.logger.info(f"✅ Hoàn tất lồng tiếng: {final_audio_path}")
            return TTSResult(success=True, audio_path=str(final_audio_path))

        except Exception as e:
            self.logger.error(f"Lỗi Edge-TTS: {e}")
            return TTSResult(success=False, error=str(e))