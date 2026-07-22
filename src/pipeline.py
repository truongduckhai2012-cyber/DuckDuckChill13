#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline Module
===============
Kết nối toàn bộ các bước: Tải video -> STT -> Dịch -> TTS -> Render.
"""

import os
import logging
from pathlib import Path
from typing import Optional

from .utils import ensure_dir, get_safe_filename, ProgressTracker, cleanup_temp_files
from .downloader import VideoDownloader
from .transcriber import FasterWhisperTranscriber, WhisperTranscriber
from .translator import TranslatorFactory
from .tts_engine import EdgeTTSEngine
from .video_renderer import VideoRenderer


class VideoTranslationPipeline:
    """Quản lý toàn bộ luồng xử lý tự động hóa dịch video."""

    def __init__(
        self,
        source_lang: str = "auto",
        target_lang: str = "vi",
        whisper_model: str = "base",
        tts_voice: Optional[str] = None,
        subtitle_style: str = "default",
        translate_engine: str = "google",
        openai_api_key: Optional[str] = None,
        deepseek_api_key: Optional[str] = None,
        video_quality: str = "best[height<=1080]",
        audio_quality: str = "bestaudio/best",
        output_dir: str = "output",
        temp_dir: str = "temp",
        download_dir: str = "downloads",
        keep_temp: bool = False,
        verbose: bool = False,
        logger: Optional[logging.Logger] = None
    ):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.whisper_model = whisper_model
        self.tts_voice = tts_voice
        self.subtitle_style = subtitle_style
        self.translate_engine = translate_engine
        self.openai_api_key = openai_api_key
        self.deepseek_api_key = deepseek_api_key
        self.video_quality = video_quality
        self.audio_quality = audio_quality
        self.output_dir = ensure_dir(output_dir)
        self.temp_dir = ensure_dir(temp_dir)
        self.download_dir = ensure_dir(download_dir)
        self.keep_temp = keep_temp
        self.verbose = verbose
        self.logger = logger or logging.getLogger("Pipeline")

    def run(self, url: str, subtitle_only: bool = False, dub_only: bool = False, skip_download: bool = False) -> dict:
        """Chạy toàn bộ pipeline xử lý video."""
        tracker = ProgressTracker(total_steps=6)
        
        try:
            # -------------------------------------------------------------
            # BƯỚC 1: Tải video và trích xuất âm thanh
            # -------------------------------------------------------------
            tracker.next_step("Tải video và trích xuất âm thanh")
            downloader = VideoDownloader(
                download_dir=str(self.download_dir),
                temp_dir=str(self.temp_dir),
                video_quality=self.video_quality,
                audio_quality=self.audio_quality,
                logger=self.logger
            )
            dl_result = downloader.download(url, skip_download=skip_download)
            if not dl_result.success:
                return {"success": False, "error": f"Lỗi tải video: {dl_result.error}"}

            video_path = dl_result.video_path
            audio_path = dl_result.audio_path
            title = dl_result.title
            self.logger.info(f"Đã sẵn sàng video: {video_path}")

            # -------------------------------------------------------------
            # BƯỚC 2: Nhận diện giọng nói (Speech-to-Text bằng Whisper)
            # -------------------------------------------------------------
            tracker.next_step("Nhận diện giọng nói (Whisper STT)")
            lang_to_pass = None if self.source_lang == "auto" else self.source_lang
            
            # Sử dụng faster-whisper để có tốc độ tối ưu
            transcriber = FasterWhisperTranscriber(
                model_size=self.whisper_model,
                language=lang_to_pass,
                logger=self.logger
            )
            stt_result = transcriber.transcribe(audio_path)
            
            if not stt_result.success or not stt_result.segments:
                # Fallback sang whisper chuẩn nếu faster-whisper lỗi
                self.logger.warning("Thử chuyển sang Whisper chuẩn...")
                transcriber_fallback = WhisperTranscriber(
                    model_size=self.whisper_model,
                    language=lang_to_pass,
                    logger=self.logger
                )
                stt_result = transcriber_fallback.transcribe(audio_path)
                if not stt_result.success or not stt_result.segments:
                    return {"success": False, "error": f"Không thể nhận diện giọng nói: {stt_result.error}"}

            # Lưu file phụ đề gốc (.srt) vào temp
            original_srt = self.temp_dir / f"{get_safe_filename(title, 'srt')}"
            stt_result.save_srt(str(original_srt))

            # -------------------------------------------------------------
            # BƯỚC 3: Dịch phụ đề sang ngôn ngữ đích
            # -------------------------------------------------------------
            tracker.next_step(f"Dịch văn bản sang [{self.target_lang}]")
            translator = TranslatorFactory.create(
                engine=self.translate_engine,
                source_lang=stt_result.language,
                target_lang=self.target_lang,
                openai_api_key=self.openai_api_key,
                deepseek_api_key=self.deepseek_api_key,
                logger=self.logger
            )
            translated_segments = translator.translate_segments(stt_result.segments)

            # Lưu file SRT dịch
            translated_srt = self.output_dir / f"{Path(get_safe_filename(title)).stem}_sub_{self.target_lang}.srt"
            from .transcriber import TranscriptionResult
            t_res = TranscriptionResult(segments=translated_segments, language=self.target_lang, text="", duration=0, success=True)
            t_res.save_srt(str(translated_srt))

            # Nếu chỉ chọn tạo phụ đề (subtitle-only), có thể dừng ở đây hoặc render sub cứng
            dubbed_audio_path = None

            # -------------------------------------------------------------
            # BƯỚC 4: Tổng hợp giọng đọc lồng tiếng (TTS)
            # -------------------------------------------------------------
            if not subtitle_only:
                tracker.next_step("Tổng hợp giọng đọc lồng tiếng (Edge-TTS)")
                tts = EdgeTTSEngine(
                    voice=self.tts_voice,
                    language=self.target_lang,
                    logger=self.logger
                )
                tts_result = tts.synthesize_segments(
                    segments=translated_segments,
                    output_dir=str(self.temp_dir),
                    sync_timing=True
                )
                if not tts_result.success:
                    self.logger.warning(f"Lồng tiếng thất bại ({tts_result.error}), tiếp tục chỉ với phụ đề.")
                else:
                    dubbed_audio_path = tts_result.audio_path
            else:
                self.logger.info("Chế độ --subtitle-only được bật, bỏ qua bước lồng tiếng.")

            # -------------------------------------------------------------
            # BƯỚC 5: Render video hoàn chỉnh bằng FFmpeg
            # -------------------------------------------------------------
            tracker.next_step("Render video cuối cùng (FFmpeg)")
            renderer = VideoRenderer(
                subtitle_style=self.subtitle_style,
                logger=self.logger
            )
            
            output_filename = f"{Path(get_safe_filename(title)).stem}_translated_{self.target_lang}.mp4"
            final_output_path = self.output_dir / output_filename

            render_result = renderer.render(
                video_path=video_path,
                output_path=str(final_output_path),
                subtitle_segments=translated_segments if not dub_only else None,
                dubbed_audio_path=dubbed_audio_path if not subtitle_only else None,
                subtitle_only=subtitle_only,
                dub_only=dub_only,
                temp_dir=str(self.temp_dir)
            )

            if not render_result.success:
                return {"success": False, "error": f"Lỗi render video: {render_result.error}"}

            # -------------------------------------------------------------
            # BƯỚC 6: Dọn dẹp file tạm
            # -------------------------------------------------------------
            tracker.next_step("Dọn dẹp hệ thống")
            cleanup_temp_files(str(self.temp_dir), keep=self.keep_temp, logger=self.logger)
            tracker.finish()

            return {
                "success": True,
                "output_path": str(final_output_path),
                "subtitle_path": str(translated_srt)
            }

        except Exception as e:
            self.logger.error(f"Lỗi không mong muốn trong Pipeline: {e}", exc_info=self.verbose)
            return {"success": False, "error": str(e)}