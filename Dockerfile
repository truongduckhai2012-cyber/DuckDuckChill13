FROM python:3.10-slim

# Cài đặt các công cụ hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cài đặt trực tiếp toàn bộ thư viện cốt lõi vào thẳng container (bỏ qua bước đọc file txt)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    streamlit \
    faster-whisper \
    edge-tts \
    yt-dlp \
    requests \
    python-dotenv

# Sao chép toàn bộ mã nguồn dự án vào
COPY . .

ENV PORT=8501
EXPOSE 8501

CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT} --server.address=0.0.0.0 --server.headless=true"]