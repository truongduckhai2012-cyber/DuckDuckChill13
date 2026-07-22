#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Translator Module
=================
Hỗ trợ dịch thuật văn bản qua Google Translate, OpenAI GPT, và DeepSeek.
"""

import os
import logging
from typing import List, Optional
from .transcriber import Segment


class BaseTranslator:
    def translate_segments(self, segments: List[Segment]) -> List[Segment]:
        raise NotImplementedError


class GoogleTranslatorEngine(BaseTranslator):
    """Dịch vụ dịch thuật miễn phí sử dụng deep-translator."""

    def __init__(self, source_lang: str, target_lang: str, logger: logging.Logger = None):
        self.source_lang = source_lang if source_lang != "auto" else "auto"
        self.target_lang = target_lang
        self.logger = logger or logging.getLogger("GoogleTranslate")

    def translate_segments(self, segments: List[Segment]) -> List[Segment]:
        try:
            from deep_translator import GoogleTranslator
            translator = GoogleTranslator(source=self.source_lang, target=self.target_lang)
            
            self.logger.info(f"🌐 Đang dịch {len(segments)} đoạn bằng Google Translate...")
            translated = []
            
            # Gom text để dịch batch hoặc dịch từng đoạn an toàn
            for seg in segments:
                translated_text = translator.translate(seg.text) or seg.text
                translated.append(Segment(id=seg.id, start=seg.start, end=seg.end, text=translated_text))

            self.logger.info("✅ Dịch hoàn tất!")
            return translated
        except Exception as e:
            self.logger.error(f"Lỗi Google Translate: {e}")
            return segments


class OpenAITranslatorEngine(BaseTranslator):
    """Dịch thuật cao cấp sử dụng OpenAI GPT."""

    def __init__(self, source_lang: str, target_lang: str, api_key: str = None, logger: logging.Logger = None):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.logger = logger or logging.getLogger("OpenAITranslate")

    def translate_segments(self, segments: List[Segment]) -> List[Segment]:
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            self.logger.info(f"🌐 Đang dịch bằng OpenAI GPT...")

            # Gộp text để gửi prompt
            texts = [s.text for s in segments]
            prompt = f"Translate the following subtitle segments from {self.source_lang} to {self.target_lang}. Keep the exact line count and order:\n" + "\n".join([f"{i+1}. {t}" for i, t in enumerate(texts)])

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            result_text = response.choices[0].message.content
            
            # Xử lý kết quả trả về đơn giản
            lines = [line.split(".", 1)[1].strip() for line in result_text.split("\n") if "." in line]
            
            translated = []
            for i, seg in enumerate(segments):
                t_text = lines[i] if i < len(lines) else seg.text
                translated.append(Segment(id=seg.id, start=seg.start, end=seg.end, text=t_text))

            return translated
        except Exception as e:
            self.logger.error(f"Lỗi OpenAI Translate: {e}")
            return segments


class DeepSeekTranslatorEngine(BaseTranslator):
    """Dịch thuật thông minh sử dụng DeepSeek API."""

    def __init__(self, source_lang: str, target_lang: str, api_key: str = None, logger: logging.Logger = None):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.logger = logger or logging.getLogger("DeepSeekTranslate")

    def translate_segments(self, segments: List[Segment]) -> List[Segment]:
        try:
            import openai
            # DeepSeek sử dụng OpenAI compatible client
            client = openai.OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com")
            self.logger.info(f"🌐 Đang dịch bằng DeepSeek...")

            texts = [s.text for s in segments]
            prompt = f"Translate the following subtitle segments from {self.source_lang} to {self.target_lang}. Keep order:\n" + "\n".join([f"{i+1}. {t}" for i, t in enumerate(texts)])

            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            result_text = response.choices[0].message.content
            lines = [line.split(".", 1)[1].strip() for line in result_text.split("\n") if "." in line]

            translated = []
            for i, seg in enumerate(segments):
                t_text = lines[i] if i < len(lines) else seg.text
                translated.append(Segment(id=seg.id, start=seg.start, end=seg.end, text=t_text))

            return translated
        except Exception as e:
            self.logger.error(f"Lỗi DeepSeek Translate: {e}")
            return segments


class TranslatorFactory:
    @staticmethod
    def create(engine: str, source_lang: str, target_lang: str, openai_api_key: str = None, deepseek_api_key: str = None, logger: logging.Logger = None) -> BaseTranslator:
        if engine == "openai":
            return OpenAITranslatorEngine(source_lang, target_lang, openai_api_key, logger)
        elif engine == "deepseek":
            return DeepSeekTranslatorEngine(source_lang, target_lang, deepseek_api_key, logger)
        else:
            return GoogleTranslatorEngine(source_lang, target_lang, logger)