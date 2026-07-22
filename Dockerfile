FROM python:3.10-slim

# Cài đặt ffmpeg và các công cụ hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Sao chép và cài đặt các thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn vào
COPY . .

ENV PORT=8501

# Chạy streamlit bằng python -m để tránh lỗi not found
CMD python -m streamlit run app.py --server.port=${PORT} --server.address=0.0.0.0 --server.headless=true