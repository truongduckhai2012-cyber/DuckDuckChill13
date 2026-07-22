#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Transcriber Module
==================
Nhận diện giọng nói (Speech-to-Text) sử dụng OpenAI Whisper và Faster-Whisper.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, NamedTuple


class Segment(NamedTuple):
    id: int
    start: float
    end: float
    text: str


class TranscriptionResult(NamedTuple):
    segments: List[Segment]
    language: str
    text: str
    duration: float
    success: bool
    error: Optional[str] = None

    def save_srt(self, filepath: str):
        """Lưu kết quả thành file phụ đề SRT."""
        with open(filepath, "w", encoding="utf-8") as f:
            for seg in self.segments:
                f.write(f"{seg.id}\n")
                f.write(f"{self._format_time(seg.start)} --> {self._format_time(seg.end)}\n")
                f.write(f"{seg.text.strip()}\n\n")

    def save_json(self, filepath: str):
        """Lưu kết quả thành file JSON."""
        import json
        data = {
            "language": self.language,
            "text": self.text,
            "duration": self.duration,
            "segments": [{"id": s.id, "start": s.start, "end": s.end, "text": s.text} for s in self.segments]
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _format_time(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int(int((seconds - int(seconds)) * 1000))
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


class FasterWhisperTranscriber:
    """Speech-to-Text sử dụng faster-whisper (tối ưu tốc độ)."""

    def __init__(self, model_size: str = "base", language: Optional[str] = None, logger: logging.Logger = None):
        self.model_size = model_size
        self.language = language
        self.logger = logger or logging.getLogger("FasterWhisper")

    def transcribe(self, audio_path: str) -> TranscriptionResult:
        try:
            from faster_whisper import WhisperModel
            self.logger.info(f"🎙️ Đang tải model faster-whisper [{self.model_size}]...")
            
            # Tự động chọn CPU/GPU
            model = WhisperModel(self.model_size, device="auto", compute_type="auto")
            
            self.logger.info(f"🎙️ Đang nhận diện giọng nói từ âm thanh...")
            segments_iter, info = model.transcribe(
                audio_path,
                language=self.language,
                beam_size=5,
                vad_filter=True
            )

            segments = []
            full_text = []
            for i, seg in enumerate(segments_iter, start=1):
                segments.append(Segment(id=i, start=seg.start, end=seg.end, text=seg.text))
                full_text.append(seg.text)

            detected_lang = info.language
            self.logger.info(f"✅ Nhận diện thành công ({len(segments)} đoạn, ngôn ngữ: {detected_lang})")

            return TranscriptionResult(
                segments=segments,
                language=detected_lang,
                text=" ".join(full_text),
                duration=info.duration,
                success=True
            )

        except Exception as e:
            self.logger.error(f"Lỗi faster-whisper: {e}")
            return TranscriptionResult(segments=[], language="en", text="", duration=0, success=False, error=str(e))


class WhisperTranscriber:
    """Speech-to-Text sử dụng thư viện openai-whisper chuẩn."""

    def __init__(self, model_size: str = "base", language: Optional[str] = None, logger: logging.Logger = None):
        self.model_size = model_size
        self.language = language
        self.logger = logger or logging.getLogger("Whisper")

    def transcribe(self, audio_path: str) -> TranscriptionResult:
        try:
            import whisper
            self.logger.info(f"🎙️ Đang tải model whisper chuẩn [{self.model_size}]...")
            model = whisper.load_model(self.model_size)

            self.logger.info(f"🎙️ Đang nhận diện giọng nói...")
            result = model.transcribe(audio_path, language=self.language)

            segments = []
            for i, seg in enumerate(result.get("segments", []), start=1):
                segments.append(Segment(id=i, start=seg["start"], end=seg["end"], text=seg["text"]))

            detected_lang = result.get("language", "en")
            self.logger.info(f"✅ Nhận diện thành công ({len(segments)} đoạn, ngôn ngữ: {detected_lang})")

            return TranscriptionResult(
                segments=segments,
                language=detected_lang,
                text=result.get("text", ""),
                duration=result.get("duration", 0.0),
                success=True
            )

        except Exception as e:
            self.logger.error(f"Lỗi whisper: {e}")
            return TranscriptionResult(segments=[], language="en", text="", duration=0, success=False, error=str(e))